"""FastAPI Endpoints untuk KeyQuiz."""
import json
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import TIPE_GAMBAR, UKURAN_MAKS_GAMBAR
from app.services import embedding_service as es
from app.services import scan_service as ss
from app.services.essay_service import nilai_esai

router = APIRouter()


class KunciIn(BaseModel):
    id_kunci: str          # id KUNCI_JAWABAN_ESSAY
    id_soal: str           # id SOAL
    soal: str
    kunci_teks: str
    rubrik: list[str]


class JawabanIn(BaseModel):
    id_detail: str         # id DETAIL_JAWABAN
    id_soal: str
    jawaban_teks: str


@router.post("/kunci", summary="Simpan Kunci Jawaban & Rubrik ke ChromaDB")
def simpan_kunci(data: KunciIn):
    es.simpan_kunci(data.id_kunci, data.id_soal, data.soal, data.kunci_teks, data.rubrik)
    return {"status": "success", "pesan": "Kunci jawaban dan rubrik berhasil disimpan"}


@router.post("/nilai", summary="Penilaian Jawaban Esai Mahasiswa")
def nilai_jawaban(data: JawabanIn):
    try:
        return nilai_esai(data.id_detail, data.id_soal, data.jawaban_teks)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/scan", summary="Scan Lembar Jawaban Kertas (Pilihan Ganda / Esai)")
def scan_jawaban(
    file: UploadFile = File(...),
    jenis: str = Form("pilihan_ganda"),   # "pilihan_ganda" atau "esai"
    kunci: str = Form(None),              # JSON string, contoh: {"1":"a","2":"c"}
    total_soal: int = Form(None),         # Jumlah total soal ujian
):
    if file.content_type not in TIPE_GAMBAR:
        raise HTTPException(status_code=400, detail="File harus berupa gambar JPG, PNG, atau WEBP")
    if jenis not in ("pilihan_ganda", "esai"):
        raise HTTPException(status_code=400, detail="Jenis harus 'pilihan_ganda' atau 'esai'")

    data = file.file.read()
    if len(data) > UKURAN_MAKS_GAMBAR:
        raise HTTPException(status_code=413, detail="Ukuran gambar maksimal 10 MB")

    kunci_dict = None
    if kunci:
        try:
            kunci_dict = json.loads(kunci)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Format kunci bukan JSON yang valid")

    try:
        terbaca = ss.baca_foto(data, jenis)
    except (json.JSONDecodeError, KeyError, ValueError):
        raise HTTPException(status_code=502, detail="Hasil baca AI tidak valid, coba foto ulang")

    if jenis == "esai":
        return {"jenis": jenis, "jawaban_terbaca": terbaca}

    hasil = {
        "jenis": jenis,
        "jawaban_terbaca": terbaca,
        "perlu_dicek": [j["nomor"] for j in terbaca if not j["yakin"]],
    }
    if kunci_dict:
        hasil["hasil_penilaian"] = ss.nilai_pilihan_ganda(terbaca, kunci_dict, total_soal=total_soal)
    return hasil
