# ⚖️ Jolly LLB — Indian Law RAG Assistant

A local **AI legal assistant** that answers natural-language questions about Indian law using a **Retrieval-Augmented Generation (RAG)** pipeline. It runs fully locally (no external APIs) and produces grounded answers with citations.

> **Note**: The stack is designed to run locally using **Docker + Ollama**.

## 🚀 Features

- 📚 Browse and query **multiple law sections** (Constitution + additional acts/sections)
- 🔎 Semantic retrieval with source citations
- 🧠 Local LLM inference with **Ollama** (default: `llama3.1:8b`)
- 📦 Vector search with **ChromaDB**
- ⚡ **FastAPI** backend API
- 💻 **React + Vite** frontend
- 🧩 **LangChain**-based RAG pipeline
- 🎯 **Cross-encoder reranking** for better relevance
- 🔒 Fully local (no cloud dependencies)
- 🧯 **Out-of-scope detection** to handle unrelated queries gracefully
- ⚡ Performance improvements for faster responses (latest updates)

## 🧠 How it works (Flow)

1. **Data ingestion**
   - Loads legal text sources (for example: `COI.json` and other datasets you add)
   - Chunks and embeds documents
2. **Vector storage**
   - Stores embeddings in **ChromaDB**
3. **Query processing**
   - Embeds the user query
   - Retrieves the most relevant chunks
   - **Cross-encoder reranking** improves relevance
   - Out-of-scope queries are detected and handled
4. **Answer generation**
   - Sends retrieved context to the Ollama LLM
   - Returns an answer with citations

## 🏗️ System architecture

```text
User (React + Vite Frontend)
        |
        v
FastAPI Backend
        |
        v
LangChain RAG Pipeline
        |
        v
ChromaDB Vector Search
        |
        v
Relevant Chunks Retrieved
        |
        v
Cross-Encoder Reranker + Out-of-scope Detection
        |
        v
Ollama LLM (llama3.1:8b)
        |
        v
Grounded Answer + Citations
```

## 🛠️ Tech stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite |
| Backend | FastAPI |
| LLM Framework | LangChain |
| Local LLM | Ollama |
| Vector Database | ChromaDB |
| Containerization | Docker |
| Language | Python |

## 📂 Project structure

```text
Jolly-LLB/
├── frontend/               # React UI
├── backend/                # API + RAG pipeline
├── docker-compose.yml
├── README.md
```

## ⚙️ Prerequisites

- Python **3.10+**
- Node.js
- Docker

## 🐳 Manual setup (Local)

### 1) Start Ollama

```bash
docker run -d \
  -p 11434:11434 \
  -v ollama:/root/.ollama \
  --name ollama \
  ollama/ollama

docker exec -it ollama ollama pull llama3.1:8b
```

### 2) Start ChromaDB

```bash
docker run -d \
  -p 8000:8000 \
  --name chromadb \
  chromadb/chroma
```

### 3) Backend setup

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

#### 📚 Ingest legal documents

Run ingestion once to embed the dataset(s) and store them in ChromaDB:

```bash
python -m app.ingest
```

### 4) Run the backend API

```bash
uvicorn app.main:app --reload --port 8080
```

API docs:
- http://localhost:8080/docs

### 5) Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on:
- http://localhost:5173

## 🧪 Example query

**Request** (`POST /query`):

```json
{
  "query": "What does the constitution say about equality?"
}
```

**Response**:

```json
{
  "answer": "Article 14 guarantees equality before the law and equal protection of the laws within the territory of India.",
  "sources": [
    {
      "article_no": "14",
      "title": "Equality before law",
      "part": "Part III - Fundamental Rights"
    }
  ]
}
```

## 🎯 Use cases

- Legal research assistants
- Law student study tools
- Civic education platforms
- AI-powered legal search

## ⚠️ Limitations

- Not a substitute for professional legal advice
- Quality depends on the datasets you ingest (coverage may be incomplete)

## 🔮 Future improvements

- Add more datasets and better metadata
- Case law retrieval
- Better ranking/grounding of citations
- Streaming responses
- Authentication + deployment

## 📜 License

MIT License
