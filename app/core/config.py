import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
RAW_DIR = "data/raw"
VECTOR_DB_PATH = "data/vector_db"
COLLECTION_NAME = "support_docs"
EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = "gemini-2.5-flash"
TOP_K_RESULTS = 5
TOP_K_FINAL = 3