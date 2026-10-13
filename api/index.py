"""Vercel Serverless Function entry point untuk FastAPI Backend KeyQuiz."""
import sys
from pathlib import Path

# Pastikan folder backend terbaca di sys.path saat dieksekusi di runtime serverless
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Import FastAPI instance
from app.main import app

# Handler untuk Vercel Serverless ASGI
handler = app
