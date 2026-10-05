"""Endpoints Pembuatan Soal Otomatis oleh AI."""
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.services.quiz_service import generate_quiz_ai

router = APIRouter(prefix="/ai", tags=["AI Task Generator"])


class QuizChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=20000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Isi pesan tidak boleh kosong")
        return value


class GenerateQuizRequest(BaseModel):
    prompt: str = Field(..., description="Instruksi bebas dosen: topik, jumlah, dan tipe soal")
    history: list[QuizChatMessage] = Field(default_factory=list)


@router.post("/generate-quiz", summary="Buat Soal & Kunci Jawaban Otomatis dengan AI")
def endpoint_generate_quiz(data: GenerateQuizRequest):
    if not data.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt tidak boleh kosong")

    try:
        kuis = generate_quiz_ai(
            prompt_text=data.prompt,
            conversation_history=[
                message.model_dump() for message in data.history
            ],
        )
        return {"status": "success", "data": kuis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal generate kuis AI: {str(e)}")
