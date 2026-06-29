import os
from dotenv import load_dotenv
from google import genai
import chromadb

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

chroma_client = chromadb.PersistentClient(path="data/vector_db")
collection = chroma_client.get_collection(name="support_docs")

query = "What is the purpose of the state vector?"

query_embedding_result = client.models.embed_content(
    model="gemini-embedding-001",
    contents=query
)
query_embedding = query_embedding_result.embeddings[0].values

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3
)

for i in range(len(results["ids"][0])):
    doc_text = results["documents"][0][i]
    metadata = results["metadatas"][0][i]
    distance = results["distances"][0][i]

    print(f"\n--- Result {i+1} (distance: {distance:.4f}) ---")
    print(f"Source: {metadata['source']} | Page: {metadata['page']}")
    print(f"Text: {doc_text[:300]}")