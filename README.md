<div align="center">



\# 🧠 Support Knowledge Copilot



\*\*Production-grade RAG API · Hybrid Retrieval · Cited Answers · FastAPI\*\*



\[!\[Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square)](https://python.org)

\[!\[FastAPI](https://img.shields.io/badge/FastAPI-0.138-green?style=flat-square)](https://fastapi.tiangolo.com)

\[!\[ChromaDB](https://img.shields.io/badge/ChromaDB-1.5.9-purple?style=flat-square)](https://trychroma.com)

\[!\[Gemini](https://img.shields.io/badge/Gemini\_API-Free\_Tier-orange?style=flat-square)](https://aistudio.google.com)



\*Ask questions about your documents. Get answers with exact source citations.\*



</div>



\---



\## What it does



Drop any PDF documents into the `data/raw/` folder. Start the API. Ask questions — get back grounded answers that cite the exact file and page number every claim came from.



```bash

POST /query  →  {"question": "What is the purpose of the state vector?"}

```



```json

{

&#x20; "question": "What is the purpose of the state vector?",

&#x20; "answer": "The objective is to estimate the motion of an object in 3D space (Source: doc1.pdf, Page: 5). The state vector captures all quantities needed since the system cannot directly measure them due to sensor noise (Source: doc1.pdf, Page: 5).",

&#x20; "sources": \[

&#x20;   { "source": "doc1.pdf", "page": 5 },

&#x20;   { "source": "doc1.pdf", "page": 9 }

&#x20; ]

}

```



\---



\## Why hybrid retrieval



Most RAG projects use only vector/semantic search. This one uses \*\*both\*\* semantic search and BM25 keyword search, fused with Reciprocal Rank Fusion — because each method has a blind spot the other covers.



| Method | Strength | Blind spot |

|---|---|---|

| Semantic search (embeddings) | Finds conceptually similar content even with different words | Misses exact terms: error codes, equation numbers, specific names |

| BM25 keyword search | Finds exact word matches reliably | Misses synonyms and paraphrase ("forgot login" ≠ "password reset") |

| \*\*RRF Fusion (this project)\*\* | \*\*Gets the best of both\*\* | — |



RRF merges the two ranked lists by position rather than raw score — the scoring scales are incomparable, so rank is the only fair common currency.



\---



\## Architecture



```

User Question

&#x20;     │

&#x20;     ├──▶ Semantic Search          BM25 Search ◀──┤

&#x20;     │    ChromaDB + Gemini        rank-bm25       │

&#x20;     │    Embeddings               keyword index   │

&#x20;     │         │                        │          │

&#x20;     └─────────┴──────────┬─────────────┘          │

&#x20;                          │                        │

&#x20;                 Reciprocal Rank Fusion             │

&#x20;                 (merge by rank position)           │

&#x20;                          │

&#x20;                    Top 3 Chunks

&#x20;                 (text + source + page)

&#x20;                          │

&#x20;                   Gemini 2.5 Flash

&#x20;                 grounded generation

&#x20;                 with inline citations

&#x20;                          │

&#x20;                   JSON Response

&#x20;              { answer, sources\[] }

```



\---



\## Tech stack



| Layer | Tool | Reason |

|---|---|---|

| PDF extraction | `pypdf` | Direct control over cleaning and metadata tagging |

| Text chunking | `RecursiveCharacterTextSplitter` | Splits at natural boundaries, preserves sentence context with overlap |

| Embeddings | Gemini `gemini-embedding-001` (3072-dim) | Free tier, top-ranked on MTEB leaderboard |

| Vector store | `ChromaDB` persistent | Local, no infrastructure needed, survives restarts |

| Keyword search | `rank-bm25` (BM25Okapi) | Same algorithm as Elasticsearch, zero API cost |

| Fusion | Reciprocal Rank Fusion | Rank-based merge, no scale normalization assumptions |

| Generation | Gemini `gemini-2.5-flash` | Free tier, fast, strong instruction-following |

| API | `FastAPI` + `uvicorn` | Auto-generates Swagger docs, production-ready |

| Testing | `pytest` | 4 automated tests covering ingestion edge cases |



\---



\## Project structure



```

support-knowledge-copilot/

├── app/

│   ├── api/main.py            # FastAPI routes — /query /health /

│   └── core/config.py         # Centralized config — models, paths, constants

├── scripts/

│   ├── ingest.py              # Load PDFs → clean → chunk → embed → store

│   ├── bm25\_retrieval.py      # BM25 index build + keyword search

│   ├── hybrid\_retrieval.py    # Semantic search + RRF fusion

│   └── generation.py          # Prompt template + Gemini call + citations

├── data/

│   ├── raw/                   # ← drop your PDFs here

│   └── vector\_db/             # ChromaDB index (auto-generated, gitignored)

├── tests/

│   └── test\_ingest.py         # Automated ingestion tests

├── .env.example               # API key template

└── requirements.txt           # Locked dependencies

```



\---



\## Setup



\*\*1 — Clone and install\*\*

```bash

git clone https://github.com/Arham8bit/support-knowledge-copilot.git

cd support-knowledge-copilot

python -m venv .venv

.venv\\Scripts\\activate        # Windows

\# source .venv/bin/activate   # Mac / Linux

pip install -r requirements.txt

```



\*\*2 — API key\*\*

```bash

cp .env.example .env

\# Add your free Google AI Studio key → https://aistudio.google.com

```



\*\*3 — Add documents\*\*

```

Drop any PDF files into  data/raw/

```



\*\*4 — Build the index\*\* \*(run once — skips automatically if already built)\*

```bash

python scripts/ingest.py

```



\*\*5 — Start the server\*\*

```bash

uvicorn app.api.main:app --reload

```



\*\*6 — Open interactive docs\*\*

```

http://127.0.0.1:8000/docs

```



\---



\## API reference



\### `POST /query`

Ask a question. Returns a grounded answer with source citations.



```json

Request   { "question": "string" }



Response  {

&#x20;           "question": "string",

&#x20;           "answer":   "string  (with inline citations)",

&#x20;           "sources":  \[ { "source": "filename.pdf", "page": 0 } ]

&#x20;         }

```



\### `GET /health`

Confirm the server is up and the index is loaded.

```json

{ "status": "healthy", "chunks\_indexed": 215 }

```



\### `GET /`

API info and endpoint listing.



\---



\## Tests



```bash

pytest tests/

\# 4 passed in 0.87s

```



Covers: whitespace cleaning, edge cases (blank pages, None text), chunking metadata preservation, empty input handling.



\---



\## Engineering decisions



\*\*Manual ingestion over LangChain wrappers\*\* — `Chroma.from\_documents()` abstracts batching and retry logic. Building it manually exposed rate-limit handling and metadata tagging decisions that matter when debugging production failures — and taught what the abstraction is actually doing.



\*\*800-char chunks with 100-char overlap\*\* — overlap prevents semantically important sentences at chunk boundaries from being split across two chunks, losing context in both. 800 characters keeps chunks focused enough for precise retrieval without being too narrow.



\*\*RRF over score normalization\*\* — BM25 scores and cosine distances have different scales and non-comparable distributions. Normalizing them requires assumptions that don't hold reliably across document types. Rank position is the only fair common denominator.



\*\*Skip-if-exists on ingestion\*\* — re-running `ingest.py` checks `collection.count()` before calling the embedding API. Avoids burning free-tier quota re-embedding unchanged documents.

