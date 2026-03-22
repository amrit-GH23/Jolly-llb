import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "Llama3.1:8B ")
EMBED_MODEL = os.getenv("EMBED_MODEL", "Llama3.1:8B ")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "indian_constitution")
CHROMA_PARENT_COLLECTION = os.getenv("CHROMA_PARENT_COLLECTION", "indian_constitution_parents")

# Cross-encoder model for reranking (downloaded automatically on first use)
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

# Child chunk settings for hierarchical chunking (approximate token counts via char ratio)
CHILD_CHUNK_SIZE = int(os.getenv("CHILD_CHUNK_SIZE", "800"))       
CHILD_CHUNK_OVERLAP = int(os.getenv("CHILD_CHUNK_OVERLAP", "200"))  

# ChromaDB stores data locally in this folder (no server needed)
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_data")
