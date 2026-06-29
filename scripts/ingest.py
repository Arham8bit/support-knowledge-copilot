import os
import re
import chromadb
import time
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    return text.strip()


def load_pdfs(raw_dir):
    pdf_files = [f for f in os.listdir(raw_dir) if f.endswith(".pdf")]
    documents = []

    for filename in pdf_files:
        filepath = os.path.join(raw_dir, filename)
        reader = PdfReader(filepath)

        for page_number, page in enumerate(reader.pages, start=1):
            cleaned = clean_text(page.extract_text())
            documents.append({
                "source": filename,
                "page": page_number,
                "text": cleaned
            })

    return documents


def chunk_documents(documents, chunk_size=800, chunk_overlap=100):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = []
    for doc in documents:
        split_texts = splitter.split_text(doc["text"])
        for i, chunk_text in enumerate(split_texts):
            chunks.append({
                "source": doc["source"],
                "page": doc["page"],
                "chunk_index": i,
                "text": chunk_text
            })

    return chunks


def embed_chunks(chunks, batch_size=20, max_retries=5):
    texts = [chunk["text"] for chunk in chunks]
    embedded_chunks = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        for attempt in range(max_retries):
            try:
                result = client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=batch
                )
                break  # success, exit the retry loop
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    wait_time = 35
                    print(f"Rate limited. Waiting {wait_time}s before retry (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    raise  # if it's a different kind of error, don't hide it, crash loudly

        for j, embedding_obj in enumerate(result.embeddings):
            chunk_copy = chunks[i + j].copy()
            chunk_copy["embedding"] = embedding_obj.values
            embedded_chunks.append(chunk_copy)

        print(f"Embedded {min(i + batch_size, len(texts))}/{len(texts)} chunks")
        time.sleep(5)  # longer pause between batches to respect the per-minute limit

    return embedded_chunks
def store_in_chromadb(embedded_chunks, db_path="data/vector_db", collection_name="support_docs"):
    chroma_client = chromadb.PersistentClient(path=db_path)
    collection = chroma_client.get_or_create_collection(name=collection_name)

    ids = []
    embeddings = []
    metadatas = []
    documents = []

    for idx, chunk in enumerate(embedded_chunks):
        ids.append(f"chunk_{idx}")
        embeddings.append(chunk["embedding"])
        metadatas.append({
            "source": chunk["source"],
            "page": chunk["page"],
            "chunk_index": chunk["chunk_index"]
        })
        documents.append(chunk["text"])

    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=documents
    )

    print(f"Stored {len(ids)} chunks in ChromaDB at '{db_path}'")
    return collection

if __name__ == "__main__":
    DB_PATH = "data/vector_db"
    COLLECTION_NAME = "support_docs"

    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    if collection.count() > 0:
        print(f"Collection already has {collection.count()} chunks. Skipping ingestion.")
        print("Delete the 'data/vector_db' folder if you want to rebuild from scratch.")
    else:
        RAW_DIR = "data/raw"
        documents = load_pdfs(RAW_DIR)
        print(f"Total pages collected: {len(documents)}")

        chunks = chunk_documents(documents)
        print(f"Total chunks created: {len(chunks)}")

        embedded_chunks = embed_chunks(chunks)
        print(f"Total embedded chunks: {len(embedded_chunks)}")

        collection = store_in_chromadb(embedded_chunks, db_path=DB_PATH, collection_name=COLLECTION_NAME)
        print(f"Collection count: {collection.count()}")