---
title: Support Knowledge Copilot
emoji: 🧠
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
license: mit
---

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

PDF Upload↓Hybrid Retrieval↓Grounded Answer↓Verified Citations
---

# 💬 Example

### Request

```http
POST /query
JSON{
  "question": "What is the purpose of the state vector?"
}
ResponseJSON{
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
❓ Why Hybrid Retrieval?Most introductory RAG projects rely solely on vector search. This project instead combines two complementary retrieval techniques.Semantic SearchUses embeddings to retrieve text with similar meaning.Example:"I forgot my login"can successfully retrieve"Reset your password"even though the wording is different.BM25 Keyword SearchFinds exact keyword matches.Useful for questions such as:Equation 15Error Code 500API KeyConfiguration Filewhere semantic embeddings often perform poorly.Reciprocal Rank Fusion (RRF)Instead of combining incompatible similarity scores, RRF merges the ranked retrieval lists based solely on their positions.This avoids score normalization issues while improving recall.🏗 ArchitecturePlaintext                    ┌────────────────────┐
                    │   User Question    │
                    └─────────┬──────────┘
                              │
               ┌──────────────┴──────────────┐
               │                             │
               ▼                             ▼
      Semantic Search               BM25 Search
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
🔄 End-to-End WorkflowPlaintextPDF Documents
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
🛠 Tech StackCategoryTechnologyBackendFastAPI, UvicornPDF ProcessingpypdfChunkingLangChain RecursiveCharacterTextSplitterEmbeddingsGemini Embedding-001Vector DatabaseChromaDBKeyword Retrievalrank-bm25Hybrid SearchReciprocal Rank FusionLLMGemini 2.5 FlashTestingPytest📂 Project StructurePlaintextsupport-knowledge-copilot/
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
🚀 Getting Started1. Clone the RepositoryBashgit clone [https://github.com/Arham8bit/support-knowledge-copilot.git](https://github.com/Arham8bit/support-knowledge-copilot.git)

cd support-knowledge-copilot
2. Create a Virtual EnvironmentWindowsBashpython -m venv .venv

.venv\Scripts\activate
Mac/LinuxBashpython3 -m venv .venv

source .venv/bin/activate
3. Install DependenciesBashpip install -r requirements.txt
4. Configure Environment VariablesCopy the example file.Bashcp .env.example .env
Add your Google AI Studio API key.GOOGLE_API_KEY=your_api_key_here
5. Add PDF DocumentsPlace your PDF files insidePlaintextdata/raw/
6. Build the Vector IndexBashpython scripts/ingest.py
The ingestion pipeline:extracts textcleans documentscreates chunksgenerates embeddingsstores vectors in ChromaDBExisting documents are skipped automatically.7. Start the APIBashuvicorn app.api.main:app --reload
8. Open Interactive API Docs[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
📡 APIPOST /queryAsk questions about your documents.RequestJSON{
  "question":"your question"
}
ResponseJSON{
  "question":"your question",
  "answer":"Grounded answer with citations",
  "sources":[
      {
         "source":"document.pdf",
         "page":5
      }
  ]
}
GET /healthReturns server status.JSON{
  "status":"healthy",
  "chunks_indexed":215
}
GET /Displays available API endpoints.🧪 Running TestsRun all tests.Bashpytest tests/
Current tests cover ingestion pipeline edge cases.⚙ Engineering DecisionsInstead of relying entirely on LangChain abstractions, the embedding pipeline was implemented manually to gain experience with batching, retry logic, metadata preservation, and debugging production issues.Chunk overlap prevents important information from being split across chunk boundaries. A chunk size of 800 characters preserves semantic context while remaining focused enough for accurate retrieval.Semantic similarity scores and BM25 scores are measured on different scales. RRF combines retrieval results using rank positions instead of raw scores, making it robust without requiring score normalization.🚧 Future ImprovementsCross-Encoder Re-rankingOCR SupportDocker DeploymentAuthenticationStreaming ResponsesMulti-user Knowledge BasesChat HistoryDocument Versioning📄 LicenseThis project is released under the MIT License.