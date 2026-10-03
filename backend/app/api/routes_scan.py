"""Endpoints Pemindaian Lembar Jawaban Kertas dengan Vision AI."""
import json
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from typing import Optional

from app.config import TIPE_GAMBAR, UKURAN_MAKS_GAMBAR
from app.services import scan_service as ss

router = APIRouter(prefix="/scan", tags=["Pemindaian Lembar Kertas Vision AI"])


@router.post("", summary="Scan Lembar Jawaban Kertas (Pilihan Ganda / Esai)")
def endpoint_scan_jawaban(
    file: UploadFile = File(..., description="File foto lembar jawaban (JPG/PNG/WEBP)"),
    jenis: str = Form("pilihan_ganda", description="Tipe lembar: 'pilihan_ganda' atau 'esai'"),
    kunci: Optional[str] = Form(None, description="JSON string kunci PG, contoh: {'1':'A','2':'C'}"),
    total_soal: Optional[int] = Form(None, description="Jumlah total soal pada lembar ujian"),
):
    if file.content_type not in TIPE_GAMBAR:
        raise HTTPException(
            status_code=400,
            detail=f"Format file '{file.content_type}' tidak didukung. Harap upload gambar JPG, PNG, atau WEBP."
        )

    if jenis not in ("pilihan_ganda", "esai"):
        raise HTTPException(status_code=400, detail="Parameter jenis harus 'pilihan_ganda' atau 'esai'")

    data = file.file.read()
    if len(data) > UKURAN_MAKS_GAMBAR:
        raise HTTPException(status_code=413, detail="Ukuran foto maksimal 10 MB")

    kunci_dict = None
    if kunci:
        try:
            kunci_dict = json.loads(kunci)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Format parameter kunci bukan JSON yang valid")

    try:
        terbaca = ss.baca_foto(data, jenis)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Gagal memproses gambar dengan Vision AI: {str(e)}"
        )

    if jenis == "esai":
        return {
            "status": "success",
            "jenis": jenis,
            "jawaban_terbaca": terbaca,
        }

    hasil = {
        "status": "success",
        "jenis": jenis,
        "jawaban_terbaca": terbaca,
        "perlu_dicek": [j["nomor"] for j in terbaca if not j.get("yakin", True)],
    }
    if kunci_dict:
        hasil["hasil_penilaian"] = ss.nilai_pilihan_ganda(terbaca, kunci_dict, total_soal=total_soal)

    return hasil
