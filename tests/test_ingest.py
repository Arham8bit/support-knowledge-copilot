import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from ingest import clean_text, chunk_documents


def test_clean_text_collapses_multiple_spaces():
    messy = "This   has    extra   spaces"
    result = clean_text(messy)
    assert "  " not in result  # no double-spaces should remain


def test_clean_text_handles_empty_string():
    assert clean_text("") == ""
    assert clean_text(None) == ""


def test_chunk_documents_produces_metadata():
    fake_docs = [{"source": "fake.pdf", "page": 1, "text": "A" * 2000}]
    chunks = chunk_documents(fake_docs, chunk_size=800, chunk_overlap=100)

    assert len(chunks) > 1  # 2000 chars should split into multiple chunks
    assert chunks[0]["source"] == "fake.pdf"
    assert chunks[0]["page"] == 1
    assert "chunk_index" in chunks[0]


def test_chunk_documents_empty_input():
    assert chunk_documents([]) == []