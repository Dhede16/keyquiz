"""Konfigurasi dan Environment Variables untuk KeyQuiz."""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY belum ditemukan di file .env")

# Model Configuration
NAMA_MODEL_VISION = os.getenv("NAMA_MODEL_VISION", "qwen/qwen3.8-27b")
NAMA_MODEL_LLM = os.getenv("NAMA_MODEL_LLM", "openai/gpt-oss-20b")
NAMA_MODEL_EMBEDDING = os.getenv("NAMA_MODEL_EMBEDDING", "all-MiniLM-L6-v2")

# Database & Storage
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

# Image constraints
TIPE_GAMBAR = ("image/jpeg", "image/png", "image/webp")
UKURAN_MAKS_GAMBAR = 10 * 1024 * 1024  # 10 MB
