import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
import chromadb

from scripts.ingest import load_pdfs, chunk_documents
from scripts.bm25_retrieval import build_bm25_index, bm25_search
from scripts.hybrid_retrieval import semantic_search, reciprocal_rank_fusion
from scripts.generation import generate_answer
from app.core.config import (
    GOOGLE_API_KEY, RAW_DIR, VECTOR_DB_PATH,
    COLLECTION_NAME, TOP_K_RESULTS, TOP_K_FINAL
)

app = FastAPI(
    title="Support Knowledge Copilot",
    description="A RAG-powered API that answers questions from your documents with citations",
    version="1.0.0"
)

# --- Load everything once at startup, not on every request ---
print("Loading documents and building BM25 index...")
documents = load_pdfs(RAW_DIR)
chunks = chunk_documents(documents)
bm25 = build_bm25_index(chunks)
print(f"Ready. {len(chunks)} chunks indexed.")


# --- Request/Response models ---
class QueryRequest(BaseModel):
    question: str


class SourceItem(BaseModel):
    source: str
    page: int


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceItem]


# --- Routes ---
@app.get("/")
def root():
    return {
        "message": "Support Knowledge Copilot API is running",
        "endpoints": {
            "query": "POST /query",
            "health": "GET /health"
        }
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "chunks_indexed": len(chunks)
    }


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        semantic_results = semantic_search(request.question, n_results=TOP_K_RESULTS)
        bm25_results = bm25_search(bm25, chunks, request.question, n_results=TOP_K_RESULTS)
        fused = reciprocal_rank_fusion(semantic_results, bm25_results)
        top_chunks = fused[:TOP_K_FINAL]

        answer = generate_answer(request.question, top_chunks)

        sources = []
        seen = set()
        for chunk in top_chunks:
            key = (chunk["source"], chunk["page"])
            if key not in seen:
                sources.append(SourceItem(source=chunk["source"], page=chunk["page"]))
                seen.add(key)

        return QueryResponse(
            question=request.question,
            answer=answer,
            sources=sources
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))