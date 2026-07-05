import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
API_KEY = os.getenv("API_KEY")

# Use /tmp on Hugging Face Spaces (only writable directory)
# Fall back to local data/ for local development
IS_HF_SPACE = os.path.exists("/tmp") and not os.path.exists("data")

if IS_HF_SPACE:
    RAW_DIR = "/tmp/raw"
    VECTOR_DB_PATH = "/tmp/vector_db"
else:
    RAW_DIR = "data/raw"
    VECTOR_DB_PATH = "data/vector_db"

COLLECTION_NAME = "support_docs"
EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = "gemini-2.5-flash"
TOP_K_RESULTS = 5
TOP_K_FINAL = 3