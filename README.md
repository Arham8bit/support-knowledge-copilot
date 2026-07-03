---
title: Support Knowledge Copilot
emoji: 🧠
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
license: mit
---

<div align="center">

# 🧠 Support Knowledge Copilot

**Production-grade RAG API · Hybrid Retrieval · Cited Answers · FastAPI**

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.138-green?style=flat-square)](https://fastapi.tiangolo.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-1.5.9-purple?style=flat-square)](https://trychroma.com)
[![Gemini](https://img.shields.io/badge/Gemini_API-Free_Tier-orange?style=flat-square)](https://aistudio.google.com)
[![License](https://img.shields.io/badge/License-MIT-success?style=flat-square)](LICENSE)
[![HF Space](https://img.shields.io/badge/🤗%20Live%20Demo-Hugging%20Face-yellow?style=flat-square)](https://huggingface.co/spaces/pololololo/support-knowledge-copilot)

*Upload any PDF. Ask questions in plain English. Get grounded answers with exact page citations.*

**[🚀 Try the Live Demo](https://huggingface.co/spaces/pololololo/support-knowledge-copilot)**

</div>

---

## What it does

Drop any PDF into the app, ask a question, and get a cited answer that references the exact source file and page number — powered by hybrid retrieval and Gemini 2.5 Flash.

```json
POST /query  →  { "question": "What is the purpose of the state vector?" }

{
  "question": "What is the purpose of the state vector?",
  "answer": "The objective is to estimate the motion of an object in 3D space (Source: doc1.pdf, Page: 5). The state vector captures all quantities needed since sensor measurements are affected by noise (Source: doc1.pdf, Page: 5).",
  "sources": [
    { "source": "doc1.pdf", "page": 5 },
    { "source": "doc1.pdf", "page": 9 }
  ]
}
```

---

## Why hybrid retrieval

Most RAG tutorials use only vector/semantic search. This project uses **both** — because each method has a blind spot the other covers.

| Method | Strength | Blind spot |
|---|---|---|
| Semantic search (embeddings) | Finds conceptually similar content even with different words | Misses exact terms: error codes, equation numbers, specific names |
| BM25 keyword search | Finds exact word matches reliably | Misses synonyms and paraphrase ("forgot login" ≠ "password reset") |
| **RRF Fusion (this project)** | **Gets the best of both** | — |

RRF merges two ranked lists by position rather than raw score — the scoring scales are incomparable, so rank is the only fair common currency.

---

## Architecture

```
User Question
      │
      ├──▶ Semantic Search          BM25 Search
      │    ChromaDB + Gemini        rank-bm25
      │    Embeddings               keyword index
      │         │                        │
      └─────────┴──────────┬─────────────┘
                           │
                  Reciprocal Rank Fusion
                  (merge by rank position)
                           │
                     Top 3 Chunks
                  (text + source + page)
                           │
                    Gemini 2.5 Flash
                  grounded generation
                  with inline citations
                           │
                    JSON Response
               { answer, sources[] }
```

---

## Tech stack

| Layer | Tool | Reason |
|---|---|---|
| PDF extraction | `pypdf` | Direct control over cleaning and metadata tagging |
| Text chunking | `RecursiveCharacterTextSplitter` | Splits at natural boundaries with overlap |
| Embeddings | Gemini `gemini-embedding-001` (3072-dim) | Free tier, strong quality |
| Vector store | `ChromaDB` persistent | Local, no infrastructure needed |
| Keyword search | `rank-bm25` (BM25Okapi) | Same algorithm as Elasticsearch, zero API cost |
| Fusion | Reciprocal Rank Fusion | Rank-based merge, no scale normalization needed |
| Generation | Gemini `gemini-2.5-flash` | Free tier, fast, strong instruction-following |
| API | `FastAPI` + `uvicorn` | Auto-generates Swagger docs, production-ready |
| Testing | `pytest` | 4 automated tests covering ingestion edge cases |

---

## Project structure

```
support-knowledge-copilot/
├── app/
│   ├── api/main.py            # FastAPI routes — /query /health /upload
│   └── core/config.py         # Centralized config — models, paths, constants
├── scripts/
│   ├── ingest.py              # Load PDFs → clean → chunk → embed → store
│   ├── bm25_retrieval.py      # BM25 index build + keyword search
│   ├── hybrid_retrieval.py    # Semantic search + RRF fusion
│   └── generation.py          # Prompt template + Gemini call + citations
├── data/
│   ├── raw/                   # ← drop your PDFs here
│   └── vector_db/             # ChromaDB index (auto-generated, gitignored)
├── frontend/
│   └── index.html             # Chat UI — upload PDFs, ask questions
├── tests/
│   └── test_ingest.py         # Automated ingestion tests
├── Dockerfile                 # Container config for HF Spaces deployment
├── .env.example               # API key template
└── requirements.txt           # Locked dependencies
```

---

## Local setup

**1 — Clone and install**
```bash
git clone https://github.com/Arham8bit/support-knowledge-copilot.git
cd support-knowledge-copilot
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac / Linux
pip install -r requirements.txt
```

**2 — API key**
```bash
cp .env.example .env
# Add your free Google AI Studio key → https://aistudio.google.com
```

**3 — Add documents and build index**
```bash
# Drop PDFs into data/raw/, then:
python scripts/ingest.py
# Skips automatically if index already exists
```

**4 — Start the server**
```bash
uvicorn app.api.main:app --reload
```

**5 — Open interactive docs or the chat UI**
```
http://127.0.0.1:8000/docs       # Swagger API docs
frontend/index.html               # Open directly in browser
```

---

## API reference

### `POST /query`
Ask a question. Optionally scope to a specific document.

```json
Request   { "question": "string", "source_filter": "filename.pdf" }

Response  {
            "question": "string",
            "answer":   "string (with inline citations)",
            "sources":  [ { "source": "filename.pdf", "page": 1 } ]
          }
```

### `POST /upload`
Upload a PDF. Automatically chunks, embeds, and indexes it.

```json
Response  { "message": "file.pdf uploaded successfully", "total_chunks": 42 }
```

### `GET /health`
```json
{ "status": "healthy", "chunks_indexed": 215 }
```

---

## Tests

```bash
pytest tests/
# 4 passed in 0.87s
```

Covers: whitespace cleaning, edge cases (blank pages, None text), chunking metadata preservation, empty input handling.

---

## Engineering decisions

**Manual ingestion over LangChain wrappers** — `Chroma.from_documents()` abstracts batching and retry logic. Building it manually exposed rate-limit handling and metadata tagging decisions that matter when debugging production failures.

**800-char chunks with 100-char overlap** — overlap prevents semantically important sentences at chunk boundaries from being split across two chunks, losing context in both.

**RRF over score normalization** — BM25 scores and cosine distances have incomparable scales and distributions. Rank position is the only fair common denominator.

**Skip-if-exists on ingestion** — re-running `ingest.py` checks `collection.count()` before calling the embedding API, avoiding wasted quota on unchanged data.

---

## Live demo

🤗 **[huggingface.co/spaces/pololololo/support-knowledge-copilot](https://huggingface.co/spaces/pololololo/support-knowledge-copilot)**

Upload any PDF → ask a question → get a cited answer.