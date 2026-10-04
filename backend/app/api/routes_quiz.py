"""Endpoints Pembuatan Soal Otomatis oleh AI."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.quiz_service import generate_quiz_ai

router = APIRouter(prefix="/ai", tags=["AI Task Generator"])


class GenerateQuizRequest(BaseModel):
    prompt: str = Field(..., description="Instruksi bebas dosen: topik, jumlah, dan tipe soal")


@router.post("/generate-quiz", summary="Buat Soal & Kunci Jawaban Otomatis dengan AI")
def endpoint_generate_quiz(data: GenerateQuizRequest):
    if not data.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt tidak boleh kosong")

    try:
        kuis = generate_quiz_ai(prompt_text=data.prompt)
        return {"status": "success", "data": kuis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal generate kuis AI: {str(e)}")
