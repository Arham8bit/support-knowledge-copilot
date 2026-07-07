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

## Automation — n8n ingestion pipeline

Manually uploading every new document isn't how a real support team would use this. So the ingestion path is automated end-to-end: **drop a PDF in Google Drive → it's chunked, embedded, and searchable within minutes — zero manual upload required.**

```
                    ┌─────────────────────┐
                    │   Schedule Trigger   │
                    │   (poll every 1 min) │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Google Drive Search  │
                    │  (scoped to 1 folder) │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   Download file       │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   POST /upload        │───────┐
                    │   (X-API-Key auth)    │        │  error
                    └──────────┬───────────┘        │
                          success/skipped            │
                               │                      │
                    ┌──────────▼───────────┐          │
                    │   IF: status ==       │          │
                    │   "success"?          │          │
                    └────┬─────────────┬────┘          │
                    true │             │ false          │
              ┌──────────▼──┐        (skip,       ┌────▼────────┐
              │ Discord:     │      no message)    │ Discord:    │
              │ ✅ new file  │                      │ ⚠️ failed   │
              │ indexed      │                      │ upload      │
              └──────────────┘                      └─────────────┘
```

**A second, independent workflow** runs a `GET /health` check every 10 minutes to keep the Hugging Face Space container warm — free-tier Spaces sleep after inactivity, and a cold container caused early ingestion runs to hang or time out.

```
Schedule Trigger (every 10 min) ──▶ GET /health
```

### Why this design

| Decision | Reason |
|---|---|
| Dedup handled by the backend, not n8n | The `/upload` endpoint already checks `os.path.exists()` before re-processing. An n8n "Remove Duplicates" node adds a second, stateful source of truth that can drift out of sync with the backend — filename-based dedup on the server is simpler and more transparent to debug. |
| Three-way branching (`success` / `skipped` / `error`) | A naive "did it work?" check conflates "already indexed, correctly skipped" with "failed" — you'd get false failure alerts on every re-scan of an already-processed file. The IF node explicitly checks `status == "success"` before notifying, so skipped files pass through silently. |
| `Continue (using error output)` on the HTTP Request node | Without this, a real backend error (e.g. embedding quota exhausted) would either halt the whole workflow or get silently absorbed into the normal output — indistinguishable from a success. This setting routes genuine failures to a dedicated error output, wired straight to a failure notification. |
| Separate keep-alive workflow | Keeping it independent of the ingestion workflow means a health-check failure can't block or interfere with an actual file upload in progress. |

### Setup

Workflow exports are in [`n8n/`](n8n/):
- `n8n/ingestion-pipeline.json` — Drive → dedup-safe upload → status-aware Discord notification
- `n8n/health-check.json` — keep-alive ping

To use:
1. Import both JSON files into your own n8n instance
2. Connect your own **Google Drive** and **Discord Bot** credentials
3. Replace the placeholder `X-API-Key` value in the HTTP Request node with your actual key (never commit this value directly — set it in n8n's credential/expression system instead)
4. Update the target URL in both HTTP Request nodes to your own deployed Space
5. Set both workflows to **Active**

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
| Automation | `n8n` | Drive-triggered ingestion + Discord status alerts, no manual uploads |
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
├── n8n/
│   ├── ingestion-pipeline.json  # Drive → chunk/embed → status-aware Discord notify
│   └── health-check.json       # Keep-alive ping to prevent free-tier Space sleep
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

**Automated ingestion via n8n, dedup on the backend** — the automation layer triggers uploads automatically from Google Drive, but the actual "is this already indexed?" decision lives in the FastAPI backend rather than in n8n's own stateful memory — one source of truth, easier to debug.

---

## Live demo

🤗 **[huggingface.co/spaces/pololololo/support-knowledge-copilot](https://huggingface.co/spaces/pololololo/support-knowledge-copilot)**

Upload any PDF → ask a question → get a cited answer.