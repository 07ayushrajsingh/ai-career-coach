import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = "career-coach-local-key-2026"
DB_PATH = os.path.join(BASE_DIR, "career.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

ALLOWED_EXT = [".pdf", ".docx"]
MAX_UPLOAD_MB = 5

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"