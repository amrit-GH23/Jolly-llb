"""
Jolly LLB — Hybrid Search + Reranking Pipeline
====================================================
Three-stage retrieval:

  1. Metadata-first filter  — Direct article lookup for "Article X" queries
  2. Hybrid search          — BM25 keyword + ChromaDB vector, fused via RRF
  3. Cross-encoder reranker — Score candidates, keep top 3

Returns parent (full-article) Documents ready for LLM context injection.
"""

import os
import re

import chromadb
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

from app.config import (
    OLLAMA_BASE_URL,
    EMBED_MODEL,
    CHROMA_COLLECTION,
    CHROMA_PARENT_COLLECTION,
    CHROMA_PERSIST_DIR,
    RERANKER_MODEL,
)

# ── Lazy-loaded singletons ──────────────────────────────────
_reranker: CrossEncoder | None = None
_child_store: Chroma | None = None
_parent_store: Chroma | None = None


def _get_reranker() -> CrossEncoder:
    """Load cross-encoder (cached after first call)."""
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(RERANKER_MODEL)
    return _reranker


def _get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_BASE_URL)


def _get_child_store() -> Chroma:
    """Connect to the child-chunks ChromaDB collection."""
    global _child_store
    if _child_store is None:
        persist_dir = os.path.normpath(CHROMA_PERSIST_DIR)
        _child_store = Chroma(
            persist_directory=persist_dir,
            collection_name=CHROMA_COLLECTION,
            embedding_function=_get_embeddings(),
        )
    return _child_store


def _get_parent_store() -> Chroma:
    """Connect to the parent-documents ChromaDB collection."""
    global _parent_store
    if _parent_store is None:
        persist_dir = os.path.normpath(CHROMA_PERSIST_DIR)
        _parent_store = Chroma(
            persist_directory=persist_dir,
            collection_name=CHROMA_PARENT_COLLECTION,
            embedding_function=_get_embeddings(),
        )
    return _parent_store


# ── Helper: fetch parent documents by parent_id ─────────────
def _fetch_parents(parent_ids: list[str]) -> list[Document]:
    """Retrieve full-article parent documents from the parents collection."""
    if not parent_ids:
        return []

    store = _get_parent_store()
    results = store.get(where={"parent_id": {"$in": parent_ids}}, include=["documents", "metadatas"])

    docs = []
    seen = set()
    for text, meta in zip(results["documents"], results["metadatas"]):
        pid = meta.get("parent_id", "")
        if pid not in seen:
            seen.add(pid)
            docs.append(Document(page_content=text, metadata=meta))
    return docs


# ── Stage 1: Metadata-first filter ──────────────────────────
def _extract_article_number(query: str) -> str | None:
    """Try to extract an article number from the query (e.g. 'Article 21', 'Art 370')."""
    match = re.search(r"(?:article|art\.?)\s*(\d+[A-Za-z]*)", query, re.IGNORECASE)
    return match.group(1) if match else None


def _metadata_filter(query: str) -> list[Document] | None:
    """If query references a specific article, fetch it directly from parents."""
    art_no = _extract_article_number(query)
    if art_no is None:
        return None

    store = _get_parent_store()
    results = store.get(
        where={"article_no": art_no},
        include=["documents", "metadatas"],
    )

    if not results["documents"]:
        return None

    docs = []
    for text, meta in zip(results["documents"], results["metadatas"]):
        docs.append(Document(page_content=text, metadata=meta))
    return docs


# ── Stage 2: Hybrid search (BM25 + Vector + RRF) ────────────
def _reciprocal_rank_fusion(
    ranked_lists: list[list[str]], k: int = 60
) -> list[str]:
    """
    Reciprocal Rank Fusion across multiple ranked lists of doc IDs.
    Returns IDs sorted by fused score (highest first).
    """
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=lambda x: scores[x], reverse=True)


def _hybrid_search(query: str, top_k: int = 20) -> list[Document]:
    """
    Run BM25 keyword search + ChromaDB vector search on child chunks,
    then fuse results with Reciprocal Rank Fusion.
    Returns top_k child chunk Documents.
    """
    child_store = _get_child_store()

    # ── Vector search ──────────────────────────────────────
    vector_results = child_store.similarity_search(query, k=top_k)

    # ── BM25 keyword search ────────────────────────────────
    # Fetch all child documents for BM25 corpus
    all_data = child_store.get(include=["documents", "metadatas"])
    all_texts = all_data["documents"]
    all_metas = all_data["metadatas"]

    # Build BM25 index
    tokenized_corpus = [doc.lower().split() for doc in all_texts]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)

    # Rank by BM25 score (get top_k indices)
    bm25_ranked_indices = sorted(
        range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
    )[:top_k]

    bm25_results = [
        Document(page_content=all_texts[i], metadata=all_metas[i])
        for i in bm25_ranked_indices
    ]

    # ── RRF fusion ─────────────────────────────────────────
    # Create unique IDs for fusion: parent_id + chunk_index
    def _doc_id(doc: Document) -> str:
        m = doc.metadata
        return f"{m.get('parent_id', '')}_{m.get('chunk_index', 0)}"

    vector_ids = [_doc_id(d) for d in vector_results]
    bm25_ids = [_doc_id(d) for d in bm25_results]

    fused_order = _reciprocal_rank_fusion([vector_ids, bm25_ids])

    # Build lookup from ID → Document
    doc_lookup: dict[str, Document] = {}
    for doc in vector_results + bm25_results:
        did = _doc_id(doc)
        if did not in doc_lookup:
            doc_lookup[did] = doc

    return [doc_lookup[did] for did in fused_order[:top_k] if did in doc_lookup]


# ── Stage 3: Cross-encoder reranking ────────────────────────
def _rerank(query: str, docs: list[Document], top_k: int = 3) -> list[Document]:
    """Score documents with cross-encoder and return the top_k best matches."""
    if not docs:
        return []

    reranker = _get_reranker()
    pairs = [[query, doc.page_content] for doc in docs]
    scores = reranker.predict(pairs)

    scored = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in scored[:top_k]]


# ── Public API ──────────────────────────────────────────────
def hybrid_retrieve(query: str, final_k: int = 3) -> list[Document]:
    """
    Full retrieval pipeline:
      1. Try metadata-first filter (direct article lookup)
      2. If no direct match → hybrid search (BM25 + vector + RRF)
      3. Rerank candidates with cross-encoder
      4. Map winning child chunks → parent (full article) documents

    Returns up to `final_k` parent Documents.
    """
    # Stage 1: metadata filter
    direct = _metadata_filter(query)
    if direct:
        # For direct lookups, still rerank if we got multiple articles
        if len(direct) > final_k:
            return _rerank(query, direct, top_k=final_k)
        return direct

    # Stage 2: hybrid search on child chunks
    candidates = _hybrid_search(query, top_k=20)

    if not candidates:
        return []

    # Stage 3: rerank child chunks
    best_children = _rerank(query, candidates, top_k=final_k)

    # Stage 4: map children → parent documents
    parent_ids = list({doc.metadata.get("parent_id", "") for doc in best_children})
    parents = _fetch_parents(parent_ids)

    if parents:
        return parents

    # Fallback: if parent lookup fails, return the child chunks directly
    return best_children
