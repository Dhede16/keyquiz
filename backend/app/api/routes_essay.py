"""Endpoints Penilaian Esai dan Manajemen Kunci Jawaban Vektor."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from app.services import embedding_service as es
from app.services.essay_service import nilai_esai

router = APIRouter(prefix="/essay", tags=["Penilaian Esai AI"])


class KunciEssayIn(BaseModel):
    id_kunci: str = Field(..., description="UUID Kunci Jawaban Essay (dari tabel kunci_jawaban_essay)")
    id_soal: str = Field(..., description="UUID Soal (dari tabel soal)")
    soal: str = Field(..., description="Teks pertanyaan")
    kunci_teks: str = Field(..., description="Teks kunci jawaban esai acuan")
    rubrik: List[str] = Field(default_factory=list, description="Daftar kriteria rubrik penilaian")


class JawabanEssayIn(BaseModel):
    id_detail: str = Field(..., description="UUID Detail Jawaban (dari tabel detail_jawaban)")
    id_soal: str = Field(..., description="UUID Soal")
    jawaban_teks: str = Field(..., description="Teks jawaban mahasiswa")


class BatchNilaiEssayIn(BaseModel):
    items: List[JawabanEssayIn]


@router.post("/kunci", summary="Simpan Kunci Jawaban & Rubrik ke ChromaDB")
def endpoint_simpan_kunci(data: KunciEssayIn):
    try:
        es.simpan_kunci(data.id_kunci, data.id_soal, data.soal, data.kunci_teks, data.rubrik)
        return {
            "status": "success",
            "message": "Kunci jawaban dan rubrik berhasil disimpan ke basis data vektor",
            "id_kunci": data.id_kunci,
            "id_soal": data.id_soal,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan kunci jawaban: {str(e)}")


@router.post("/nilai", summary="Penilaian Esai berdasarkan Kemiripan Embedding")
def endpoint_nilai_esai(data: JawabanEssayIn):
    try:
        return nilai_esai(data.id_detail, data.id_soal, data.jawaban_teks)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kesalahan penilaian AI: {str(e)}")


@router.post("/nilai-batch", summary="Penilaian Esai Batch berdasarkan Kemiripan Embedding")
def endpoint_nilai_esai_batch(data: BatchNilaiEssayIn):
    results = []
    for item in data.items:
        try:
            res = nilai_esai(item.id_detail, item.id_soal, item.jawaban_teks)
            results.append({"status": "success", "data": res})
        except Exception as e:
            results.append({
                "status": "error",
                "id_detail": item.id_detail,
                "id_soal": item.id_soal,
                "error": str(e),
            })
    return {"results": results}
