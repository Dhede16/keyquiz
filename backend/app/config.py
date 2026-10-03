"""Konfigurasi global dan pembacaan Environment Variables untuk Backend KeyQuiz."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cari .env dari root project jika ada, atau di backend
root_env = Path(__file__).resolve().parent.parent.parent / ".env"
backend_env = Path(__file__).resolve().parent.parent / ".env"

if root_env.exists():
    load_dotenv(dotenv_path=root_env)
elif backend_env.exists():
    load_dotenv(dotenv_path=backend_env)
else:
    load_dotenv()

# Server Config
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173").split(",")
    if origin.strip()
]

# Supabase Config
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")

# AI & LLM Config (Groq / OpenAI)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
NAMA_MODEL_VISION = os.getenv("NAMA_MODEL_VISION", "llama-3.2-11b-vision-preview")
NAMA_MODEL_LLM = os.getenv("NAMA_MODEL_LLM", "llama-3.3-70b-versatile")
NAMA_MODEL_EMBEDDING = os.getenv("NAMA_MODEL_EMBEDDING", "all-MiniLM-L6-v2")

# ChromaDB Storage
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

# Image constraints
TIPE_GAMBAR = ("image/jpeg", "image/png", "image/webp")
UKURAN_MAKS_GAMBAR = 10 * 1024 * 1024  # 10 MB
