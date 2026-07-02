<<<<<<< HEAD
# 📚 Support Knowledge Copilot

> **A production-grade Retrieval-Augmented Generation (RAG) API that answers questions from your documents using Hybrid Retrieval (Semantic Search + BM25) with verified page-level citations.**

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Production-green)
![ChromaDB](https://img.shields.io/badge/VectorDB-Chroma-orange)
![Gemini](https://img.shields.io/badge/LLM-Gemini_2.5_Flash-blueviolet)
![License](https://img.shields.io/badge/License-MIT-success)

---

## 📖 Overview

Support Knowledge Copilot is a production-ready RAG API that allows users to upload PDF documents and ask natural language questions about them.

Instead of relying solely on semantic search, this project combines **dense retrieval (embeddings)** and **sparse retrieval (BM25)** using **Reciprocal Rank Fusion (RRF)** to improve retrieval quality. Responses are generated using **Gemini 2.5 Flash** and include **page-level citations** so every answer can be verified.

---

## ✨ Features

* 📄 Upload one or multiple PDF documents
* 🤖 Ask questions in plain English
* 🔍 Hybrid Retrieval (Semantic Search + BM25)
* ⚡ Reciprocal Rank Fusion (RRF)
* 📌 Grounded responses with page-level citations
* 💾 Persistent ChromaDB vector database
* 🚀 FastAPI backend
* 📚 Interactive Swagger API documentation
* 🧪 Automated tests for the ingestion pipeline

---

## 🎥 Demo

> *(Add screenshots or a GIF here later.)*

```
PDF Upload
      ↓
Hybrid Retrieval
      ↓
Grounded Answer
      ↓
Verified Citations
```

---

# 💬 Example

### Request

```http
POST /query
```

```json
{
  "question": "What is the purpose of the state vector?"
}
```

### Response

```json
{
  "question": "What is the purpose of the state vector?",
  "answer": "The objective of defining a complete system state is to estimate the motion of an object moving in three-dimensional space (Source: doc1.pdf, Page: 5).",
  "sources": [
    {
      "source": "doc1.pdf",
      "page": 5
    },
    {
      "source": "doc1.pdf",
      "page": 9
    }
  ]
}
```

---

# ❓ Why Hybrid Retrieval?

Most introductory RAG projects rely solely on vector search. This project instead combines two complementary retrieval techniques.

### Semantic Search

Uses embeddings to retrieve text with similar meaning.

Example:

> "I forgot my login"

can successfully retrieve

> "Reset your password"

even though the wording is different.

---

### BM25 Keyword Search

Finds exact keyword matches.

Useful for questions such as:

* Equation 15
* Error Code 500
* API Key
* Configuration File

where semantic embeddings often perform poorly.

---

### Reciprocal Rank Fusion (RRF)

Instead of combining incompatible similarity scores, RRF merges the ranked retrieval lists based solely on their positions.

This avoids score normalization issues while improving recall.

---

# 🏗 Architecture

```text
                    ┌────────────────────┐
                    │   User Question    │
                    └─────────┬──────────┘
                              │
               ┌──────────────┴──────────────┐
               │                             │
               ▼                             ▼
      Semantic Search                 BM25 Search
     (Chroma + Gemini)               (rank-bm25)
               │                             │
               └──────────────┬──────────────┘
                              ▼
                Reciprocal Rank Fusion
                              │
                              ▼
                    Top Relevant Chunks
                    Source + Page Metadata
                              │
                              ▼
                     Gemini 2.5 Flash
                              │
                              ▼
              Grounded Answer + Citations
```

---

# 🔄 End-to-End Workflow

```text
PDF Documents
      │
      ▼
Text Extraction (pypdf)
      │
      ▼
Text Cleaning
      │
      ▼
Chunking
      │
      ▼
Gemini Embeddings
      │
      ▼
Store in ChromaDB
      │
─────────────────────────────────────────────
User Question
      │
      ▼
Semantic Search
      +
BM25 Search
      │
      ▼
Reciprocal Rank Fusion
      │
      ▼
Top Relevant Chunks
      │
      ▼
Gemini 2.5 Flash
      │
      ▼
Grounded Answer with Citations
```

---

# 🛠 Tech Stack

| Category          | Technology                               |
| ----------------- | ---------------------------------------- |
| Backend           | FastAPI, Uvicorn                         |
| PDF Processing    | pypdf                                    |
| Chunking          | LangChain RecursiveCharacterTextSplitter |
| Embeddings        | Gemini Embedding-001                     |
| Vector Database   | ChromaDB                                 |
| Keyword Retrieval | rank-bm25                                |
| Hybrid Search     | Reciprocal Rank Fusion                   |
| LLM               | Gemini 2.5 Flash                         |
| Testing           | Pytest                                   |

---

# 📂 Project Structure

```text
support-knowledge-copilot/
│
├── app/
│   ├── api/
│   │   └── main.py
│   └── core/
│       └── config.py
│
├── scripts/
│   ├── ingest.py
│   ├── bm25_retrieval.py
│   ├── hybrid_retrieval.py
│   └── generation.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── vector_db/
│
├── tests/
│   └── test_ingest.py
│
├── docs/
├── .env.example
├── requirements.txt
└── README.md
```

---

# 🚀 Getting Started

## 1. Clone the Repository

```bash
git clone https://github.com/Arham8bit/support-knowledge-copilot.git

cd support-knowledge-copilot
```

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv .venv

.venv\Scripts\activate
```

### Mac/Linux

```bash
python3 -m venv .venv

source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Copy the example file.

```bash
cp .env.example .env
```

Add your Google AI Studio API key.

```
GOOGLE_API_KEY=your_api_key_here
```

---

## 5. Add PDF Documents

Place your PDF files inside

```text
data/raw/
```

---

## 6. Build the Vector Index

```bash
python scripts/ingest.py
```

The ingestion pipeline:

* extracts text
* cleans documents
* creates chunks
* generates embeddings
* stores vectors in ChromaDB

Existing documents are skipped automatically.

---

## 7. Start the API

```bash
uvicorn app.api.main:app --reload
```

---

## 8. Open Interactive API Docs

```
http://127.0.0.1:8000/docs
```

---

# 📡 API

## POST `/query`

Ask questions about your documents.

### Request

```json
{
  "question":"your question"
}
```

### Response

```json
{
  "question":"your question",
  "answer":"Grounded answer with citations",
  "sources":[
      {
         "source":"document.pdf",
         "page":5
      }
  ]
}
```

---

## GET `/health`

Returns server status.

```json
{
  "status":"healthy",
  "chunks_indexed":215
}
```

---

## GET `/`

Displays available API endpoints.

---

# 🧪 Running Tests

Run all tests.

```bash
pytest tests/
```

Current tests cover ingestion pipeline edge cases.

---

# ⚙ Engineering Decisions

<details>

<summary><strong>Why not use LangChain's built-in RAG chain?</strong></summary>

Instead of relying entirely on LangChain abstractions, the embedding pipeline was implemented manually to gain experience with batching, retry logic, metadata preservation, and debugging production issues.

</details>

<details>

<summary><strong>Why chunk at 800 characters with 100-character overlap?</strong></summary>

Chunk overlap prevents important information from being split across chunk boundaries. A chunk size of 800 characters preserves semantic context while remaining focused enough for accurate retrieval.

</details>

<details>

<summary><strong>Why Reciprocal Rank Fusion?</strong></summary>

Semantic similarity scores and BM25 scores are measured on different scales. RRF combines retrieval results using rank positions instead of raw scores, making it robust without requiring score normalization.

</details>

---

# 🚧 Future Improvements

* Cross-Encoder Re-ranking
* OCR Support
* Docker Deployment
* Authentication
* Streaming Responses
* Multi-user Knowledge Bases
* Chat History
* Document Versioning

---

# 📄 License

This project is released under the MIT License.

---


=======
---
title: Support Knowledge Copilot
emoji: 🐨
colorFrom: yellow
colorTo: yellow
sdk: docker
pinned: false
license: mit
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
>>>>>>> 63d7f2a69e33fc592a58c27335173d16b31dbf60
