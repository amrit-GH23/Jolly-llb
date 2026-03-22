"""
Jolly LLB — RAG Retrieval & Synthesis
======================================
1. Hybrid retrieval → Top articles via metadata filter / BM25+vector / reranker
2. Context injection → Formatted source strings
3. System prompt → Legal assistant with strict grounding + out-of-scope handling
4. Output → { answer, sources }
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import OLLAMA_BASE_URL, LLM_MODEL
from app.hybrid_search import hybrid_retrieve

SYSTEM_PROMPT = """You are Jolly LLB, a friendly and knowledgeable Legal Assistant specialized in the Constitution of India.
Using ONLY the provided Context, answer the User Query.

Rules:
1. Start by explicitly stating which Article(s) apply.
2. Summarize the law in simple terms that a non-lawyer can understand.
3. Do not give personal opinions; stick to the text of the Constitution.
4. Always reference articles by their number and title.
5. If the User Query is clearly NOT related to law, the Indian Constitution, legal rights, governance, or anything even loosely connected to the Constitution of India, then DO NOT try to force an answer from the provided Context. Instead, politely explain that you are Jolly LLB — an AI assistant specialized in the Indian Constitution — and that this particular question falls outside your expertise. Then suggest 2-3 example questions the user could ask you instead, such as:
   - "What does Article 21 say about the right to life?"
   - "Explain the right to freedom of speech under Article 19"
   - "What are the fundamental duties of Indian citizens?"
6. However, if the query IS related to law, governance, rights, duties, or any constitutional topic — even if the provided context does not perfectly cover it — do your best to answer using the closest relevant articles from the context. If the context doesn't fully cover the topic, mention which articles are most relevant and note that the Constitution may have additional provisions not included in the current context.
7. Be helpful and conversational in tone. You are named Jolly LLB — be approachable."""


def get_legal_advice(user_query: str) -> dict:
    """
    RAG workflow:
      1. Hybrid retrieve (metadata filter → BM25+vector → rerank → parent lookup)
      2. Format context
      3. Query LLM with legal system prompt (handles out-of-scope via prompt)
      4. Return { answer, sources }
    """
    # Step 1 — Retrieve via hybrid pipeline
    docs = hybrid_retrieve(user_query, final_k=3)

    if not docs:
        return {"answer": "No relevant articles found.", "sources": []}

    # Step 2 — Format context
    context_parts = []
    sources = []
    for i, doc in enumerate(docs, 1):
        art_no = doc.metadata.get("article_no", "?")
        title = doc.metadata.get("title", "")
        part = doc.metadata.get("part", "")
        context_parts.append(f"Source {i}: Article {art_no} ({title}) [{part}]\n{doc.page_content}")
        sources.append({"article_no": art_no, "title": title, "part": part})

    context = "\n\n---\n\n".join(context_parts)

    # Step 3 — Query LLM
    llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.1)
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Context:\n{context}\n\n---\n\nUser Query: {user_query}"),
    ])

    # Step 4 — Return
    return {"answer": response.content, "sources": sources}
