"""Endpoints Penilaian Esai dan Manajemen Kunci Jawaban Vektor."""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.config import SUPABASE_SERVICE_ROLE_KEY
from app.core.supabase import get_supabase_admin
from app.services import embedding_service as es
from app.services.essay_service import nilai_esai

router = APIRouter(prefix="/essay", tags=["Penilaian Esai AI"])
logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


def authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login diperlukan.")
    if not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SUPABASE_SERVICE_ROLE_KEY belum dikonfigurasi di backend.",
        )

    admin = get_supabase_admin()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Layanan autentikasi Supabase belum tersedia.",
        )

    try:
        result = admin.auth.get_user(credentials.credentials)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi login tidak valid atau sudah berakhir.",
        ) from exc

    if not result.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi login tidak valid atau sudah berakhir.",
        )
    return result.user


def get_admin_client():
    if not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SUPABASE_SERVICE_ROLE_KEY belum dikonfigurasi di backend.",
        )
    admin = get_supabase_admin()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Layanan database Supabase belum tersedia.",
        )
    return admin


class KunciEssayIn(BaseModel):
    id_kunci: str = Field(..., description="UUID Kunci Jawaban Essay (dari tabel kunci_jawaban_essay)")
    id_soal: str = Field(..., description="UUID Soal (dari tabel soal)")
    soal: str = Field(..., description="Teks pertanyaan")
    kunci_teks: str = Field(..., description="Teks kunci jawaban esai acuan")
    rubrik: List[str] = Field(default_factory=list, description="Daftar kriteria rubrik penilaian")


class JawabanEssayIn(BaseModel):
    submission_id: str = Field(..., description="UUID pengumpulan jawaban mahasiswa")
    id_soal: str = Field(..., description="UUID Soal")


@router.post("/kunci", summary="Simpan Kunci Jawaban & Rubrik ke ChromaDB")
def endpoint_simpan_kunci(data: KunciEssayIn, user=Depends(authenticated_user)):
    try:
        admin = get_admin_client()
        question = (
            admin.table("soal")
            .select("id,tugas_id")
            .eq("id", data.id_soal)
            .maybe_single()
            .execute()
            .data
        )
        if not question:
            raise HTTPException(status_code=404, detail="Soal tidak ditemukan.")
        task = (
            admin.table("tugas")
            .select("kelas_id")
            .eq("id", question["tugas_id"])
            .single()
            .execute()
            .data
        )
        class_row = (
            admin.table("kelas")
            .select("teacher_id")
            .eq("id", task["kelas_id"])
            .single()
            .execute()
            .data
        )
        if class_row["teacher_id"] != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya dosen kelas yang dapat menyimpan kunci jawaban.",
            )

        es.simpan_kunci(data.id_kunci, data.id_soal, data.soal, data.kunci_teks, data.rubrik)
        return {
            "status": "success",
            "message": "Kunci jawaban dan rubrik berhasil disimpan ke basis data vektor",
            "id_kunci": data.id_kunci,
            "id_soal": data.id_soal,
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.exception("Gagal menyimpan kunci jawaban esai")
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan kunci jawaban: {str(e)}")


@router.post("/nilai", summary="Penilaian Esai berdasarkan Rubrik dan AI")
def endpoint_nilai_esai(data: JawabanEssayIn, user=Depends(authenticated_user)):
    try:
        admin = get_admin_client()
        submission = (
            admin.table("jawaban_mahasiswa")
            .select("id,student_id,tugas_id,status,is_scanned")
            .eq("id", data.submission_id)
            .maybe_single()
            .execute()
            .data
        )
        if not submission or submission["student_id"] != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pengumpulan jawaban tidak ditemukan.",
            )
        if submission["status"] == "graded" or submission["is_scanned"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Pengumpulan ini tidak dapat dinilai ulang oleh mahasiswa.",
            )

        question = (
            admin.table("soal")
            .select("id,tugas_id,type,question_text")
            .eq("id", data.id_soal)
            .maybe_single()
            .execute()
            .data
        )
        if (
            not question
            or question["tugas_id"] != submission["tugas_id"]
            or question["type"] not in ("essay", "short_answer")
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Soal esai tidak ditemukan pada tugas tersebut.",
            )

        answer_key = (
            admin.table("kunci_jawaban_essay")
            .select("id,answer_key,rubric")
            .eq("soal_id", data.id_soal)
            .maybe_single()
            .execute()
            .data
        )
        if not answer_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kunci jawaban esai belum tersedia.",
            )
        es.simpan_kunci(
            answer_key["id"],
            data.id_soal,
            question["question_text"],
            answer_key["answer_key"],
            answer_key["rubric"] or [],
        )

        answer = (
            admin.table("detail_jawaban")
            .select("id,jawaban_teks")
            .eq("submission_id", data.submission_id)
            .eq("soal_id", data.id_soal)
            .limit(1)
            .execute()
            .data
        )
        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Jawaban mahasiswa belum tersimpan.",
            )

        result = nilai_esai(answer[0]["id"], data.id_soal, answer[0]["jawaban_teks"] or "")
        update_result = (
            admin.table("detail_jawaban")
            .update({
                "similarity_score": result["similarity"],
                "rubric_evaluation": {
                    "rubric_results": result["rubric_results"],
                    "alasan_ai": result["alasan_ai"],
                },
                "nilai_ai": result["nilai_ai"],
            })
            .eq("id", answer[0]["id"])
            .execute()
        )
        if getattr(update_result, "error", None):
            raise RuntimeError("Gagal menyimpan hasil penilaian AI.")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Gagal menilai jawaban esai")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan saat menilai jawaban esai.")
