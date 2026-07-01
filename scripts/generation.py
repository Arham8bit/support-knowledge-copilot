import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from dotenv import load_dotenv
from google import genai
from ingest import load_pdfs, chunk_documents
from bm25_retrieval import build_bm25_index, bm25_search
from hybrid_retrieval import semantic_search, reciprocal_rank_fusion

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def build_context_block(chunks):
    context_parts = []

    for chunk in chunks:
        source = chunk["source"]
        page = chunk["page"]
        text = chunk["text"]

        context_parts.append(
            f"[Source: {source}, Page: {page}]\n{text}"
        )

    return "\n\n---\n\n".join(context_parts)


def build_prompt(question, context_block):
    return f"""You are a helpful assistant that answers questions strictly based on the provided context documents.

RULES:
- Answer ONLY using information from the context below
- After every factual claim, cite the source like this: (Source: filename, Page: X)
- If the context does not contain enough information to answer, say "I cannot find this in the provided documents"
- Be concise and clear

CONTEXT:
{context_block}

QUESTION:
{question}

ANSWER:"""


def generate_answer(question, context_chunks):
    context_block = build_context_block(context_chunks)
    prompt = build_prompt(question, context_block)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text


if __name__ == "__main__":
    RAW_DIR = "data/raw"
    documents = load_pdfs(RAW_DIR)
    chunks = chunk_documents(documents)
    bm25 = build_bm25_index(chunks)

    query = "What is the purpose of the state vector?"

    print("Retrieving relevant chunks...")
    semantic_results = semantic_search(query, n_results=5)
    bm25_results = bm25_search(bm25, chunks, query, n_results=5)
    fused_chunks = reciprocal_rank_fusion(semantic_results, bm25_results)
    top_chunks = fused_chunks[:3]

    print(f"Using {len(top_chunks)} chunks as context\n")
    print("Generating answer...\n")

    answer = generate_answer(query, top_chunks)

    print("=" * 60)
    print("QUESTION:", query)
    print("=" * 60)
    print("ANSWER:")
    print(answer)
    print("=" * 60)
    print("\nSOURCES USED:")
    for chunk in top_chunks:
        print(f"  - {chunk['source']}, Page {chunk['page']}")