import os
import re
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


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


if __name__ == "__main__":
    RAW_DIR = "data/raw"
    documents = load_pdfs(RAW_DIR)
    print(f"Total pages collected: {len(documents)}")

    chunks = chunk_documents(documents)
    print(f"Total chunks created: {len(chunks)}")

    for chunk in chunks[:3]:
        print(f"\nSource: {chunk['source']} | Page: {chunk['page']} | Chunk: {chunk['chunk_index']}")
        print(f"Text: {chunk['text'][:200]}")