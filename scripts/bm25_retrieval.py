import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from rank_bm25 import BM25Okapi
from ingest import load_pdfs, chunk_documents


def build_bm25_index(chunks):
    tokenized_corpus = [chunk["text"].lower().split() for chunk in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25


def bm25_search(bm25, chunks, query, n_results=5, source_filter=None):
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    scored_chunks = []
    for i, score in enumerate(scores):
        if score > 0:
            if source_filter and chunks[i]["source"] != source_filter:
                continue
            scored_chunks.append({
                "source": chunks[i]["source"],
                "page": chunks[i]["page"],
                "chunk_index": chunks[i]["chunk_index"],
                "text": chunks[i]["text"],
                "bm25_score": score
            })

    scored_chunks.sort(key=lambda x: x["bm25_score"], reverse=True)
    return scored_chunks[:n_results]


if __name__ == "__main__":
    RAW_DIR = "data/raw"
    documents = load_pdfs(RAW_DIR)
    chunks = chunk_documents(documents)
    bm25 = build_bm25_index(chunks)

    query = "What is the purpose of the state vector?"
    results = bm25_search(bm25, chunks, query, n_results=3)

    for i, result in enumerate(results):
        print(f"\n--- Result {i+1} (BM25 score: {result['bm25_score']:.4f}) ---")
        print(f"Source: {result['source']} | Page: {result['page']}")
        print(f"Text: {result['text'][:300]}")