"""KeyQuiz Backend Production API - FastAPI Server."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.api.router import api_router

app = FastAPI(
    title="KeyQuiz API",
    description="Sistem Penilaian Esai Berbasis AI (Semantic Similarity + LLM Rubrik) dan Pemindaian Lembar Kertas Vision AI.",
    version="1.0.0",
)

# Konfigurasi CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Daftarkan Router API
app.include_router(api_router)


@app.get("/", tags=["Health Check"])
def health_check():
    return {
        "status": "online",
        "service": "KeyQuiz Production Backend API",
        "version": "1.0.0",
        "docs": "/docs",
    }
