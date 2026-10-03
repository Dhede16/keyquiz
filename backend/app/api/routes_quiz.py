"""Endpoints Pembuatan Soal Otomatis oleh AI."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.services.quiz_service import generate_quiz_ai

router = APIRouter(prefix="/ai", tags=["AI Task Generator"])


class GenerateQuizRequest(BaseModel):
    prompt: str = Field(..., description="Topik atau instruksi materi soal")
    jumlah_pg: Optional[int] = Field(3, description="Jumlah soal pilihan ganda yang diinginkan")
    jumlah_esai: Optional[int] = Field(2, description="Jumlah soal esai yang diinginkan")


@router.post("/generate-quiz", summary="Buat Soal & Kunci Jawaban Otomatis dengan AI")
def endpoint_generate_quiz(data: GenerateQuizRequest):
    if not data.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt materi tidak boleh kosong")

    try:
        kuis = generate_quiz_ai(
            prompt_text=data.prompt,
            jumlah_pg=data.jumlah_pg or 3,
            jumlah_esai=data.jumlah_esai or 2,
        )
        return {
            "status": "success",
            "data": kuis,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal generate kuis AI: {str(e)}")
