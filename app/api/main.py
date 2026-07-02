import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse 
from fastapi.staticfiles import StaticFiles  # <-- Added to handle your frontend folder's static files
from pydantic import BaseModel
import shutil

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Graceful startup — works even if data/raw/ is empty ---
print("Starting Support Knowledge Copilot...")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(VECTOR_DB_PATH, exist_ok=True)

pdf_files = [f for f in os.listdir(RAW_DIR) if f.endswith('.pdf')]

if pdf_files:
    documents = load_pdfs(RAW_DIR)
    chunks = chunk_documents(documents)
    bm25 = build_bm25_index(chunks)
    print(f"Ready. {len(chunks)} chunks indexed.")
else:
    documents = []
    chunks = []
    bm25 = build_bm25_index([])
    print("Ready. No PDFs found — waiting for upload.")


# --- Models ---
class QueryRequest(BaseModel):
    question: str
    source_filter: str = None


class SourceItem(BaseModel):
    source: str
    page: int


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceItem]


# --- Routes & Static Configuration ---

# Path to your index.html inside the frontend folder
HTML_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "index.html"))
# Path to the frontend folder directory for mounting static files
FRONTEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

@app.get("/")
def root():
    # If the index.html exists inside frontend/, serve it directly to the browser
    if os.path.exists(HTML_PATH):
        return FileResponse(HTML_PATH)
    
    # Fallback response in case the path is slightly off
    return {
        "error": f"index.html not found at {HTML_PATH}. Please check its location.",
        "message": "Support Knowledge Copilot API is running"
    }


@app.get("/health")
def health():
    return {"status": "healthy", "chunks_indexed": len(chunks)}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    os.makedirs(RAW_DIR, exist_ok=True)
    save_path = os.path.join(RAW_DIR, file.filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    global chunks, bm25
    documents = load_pdfs(RAW_DIR)
    chunks = chunk_documents(documents)
    bm25 = build_bm25_index(chunks)

    return {
        "message": f"{file.filename} uploaded successfully",
        "filename": file.filename,
        "total_chunks": len(chunks)
    }


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if len(chunks) == 0:
        raise HTTPException(
            status_code=400,
            detail="No documents indexed yet. Please upload a PDF first."
        )

    try:
        where_filter = {"source": request.source_filter} if request.source_filter else None

        semantic_results = semantic_search(
            request.question,
            n_results=TOP_K_RESULTS,
            where=where_filter
        )
        bm25_results = bm25_search(
            bm25, chunks, request.question,
            n_results=TOP_K_RESULTS,
            source_filter=request.source_filter
        )
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

# Mount the frontend directory under the '/static' path so styles/scripts load cleanly
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")