import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from dotenv import load_dotenv
from google import genai
import chromadb
from ingest import load_pdfs, chunk_documents
from bm25_retrieval import build_bm25_index, bm25_search

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def semantic_search(query, n_results=5):
    chroma_client = chromadb.PersistentClient(path="data/vector_db")
    collection = chroma_client.get_collection(name="support_docs")

    query_embedding = client.models.embed_content(
        model="gemini-embedding-001",
        contents=query
    ).embeddings[0].values

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    hits = []
    for i in range(len(results["ids"][0])):
        hits.append({
            "source": results["metadatas"][0][i]["source"],
            "page": results["metadatas"][0][i]["page"],
            "chunk_index": results["metadatas"][0][i]["chunk_index"],
            "text": results["documents"][0][i],
            "distance": results["distances"][0][i]
        })
    return hits


def reciprocal_rank_fusion(semantic_results, bm25_results, k=60):
    scores = {}

    for rank, result in enumerate(semantic_results):
        key = (result["source"], result["page"], result["chunk_index"])
        if key not in scores:
            scores[key] = {"chunk": result, "rrf_score": 0}
        scores[key]["rrf_score"] += 1 / (rank + 1 + k)

    for rank, result in enumerate(bm25_results):
        key = (result["source"], result["page"], result["chunk_index"])
        if key not in scores:
            scores[key] = {"chunk": result, "rrf_score": 0}
        scores[key]["rrf_score"] += 1 / (rank + 1 + k)

    sorted_results = sorted(
        scores.values(),
        key=lambda x: x["rrf_score"],
        reverse=True
    )

    return [item["chunk"] for item in sorted_results]


if __name__ == "__main__":
    RAW_DIR = "data/raw"
    documents = load_pdfs(RAW_DIR)
    chunks = chunk_documents(documents)
    bm25 = build_bm25_index(chunks)

    query = "What is the purpose of the state vector?"

    print("Running semantic search...")
    semantic_results = semantic_search(query, n_results=5)

    print("Running BM25 search...")
    bm25_results = bm25_search(bm25, chunks, query, n_results=5)

    print("Fusing results...\n")
    fused = reciprocal_rank_fusion(semantic_results, bm25_results)

    print(f"Hybrid results for: '{query}'\n")
    for i, result in enumerate(fused[:3]):
        print(f"--- Result {i+1} ---")
        print(f"Source: {result['source']} | Page: {result['page']}")
        print(f"Text: {result['text'][:300]}")
        print()