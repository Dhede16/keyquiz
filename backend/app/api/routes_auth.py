"""Router autentikasi backend untuk pendaftaran akun yang terkonfirmasi."""
import logging
import re
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.core.supabase import get_supabase_admin

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


class RegisterAdminRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=120)
    role: Literal["teacher", "student"] = "student"

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Alamat email tidak valid.")
        return value

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Nama wajib diisi.")
        return value


@router.post("/register-admin")
def register_user_admin(payload: RegisterAdminRequest):
    """Mendaftarkan akun terkonfirmasi tanpa menyimpan kata sandi di profil."""
    admin = get_supabase_admin()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin client Supabase belum terkonfigurasi di backend."
        )

    try:
        res = admin.auth.admin.create_user({
            "email": payload.email,
            "password": payload.password,
            "email_confirm": True,
            "user_metadata": {
                "name": payload.name,
                "role": payload.role,
            }
        })
    except Exception as exc:
        error_code = getattr(exc, "code", "") or ""
        error_message = str(exc).lower()
        if error_code == "email_exists" or any(
            phrase in error_message
            for phrase in ("already registered", "already exists", "user already exists")
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email tersebut sudah terdaftar. Silakan masuk atau gunakan email lain."
            ) from exc
        logger.exception("Gagal membuat akun Supabase")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gagal mendaftarkan akun. Silakan coba kembali."
        ) from exc

    user_id = res.user.id if res.user else None
    if not user_id:
        logger.error("Supabase tidak mengembalikan user setelah pendaftaran")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gagal mendaftarkan akun. Silakan coba kembali."
        )

    try:
        admin.table("profiles").upsert({
            "id": user_id,
            "email": payload.email,
            "name": payload.name,
            "role": payload.role,
        }).execute()
    except Exception as exc:
        logger.exception("Gagal menyimpan profil akun baru")
        try:
            admin.auth.admin.delete_user(user_id)
        except Exception:
            logger.exception("Gagal membersihkan akun setelah profil gagal disimpan")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gagal menyimpan profil akun. Silakan coba kembali."
        ) from exc

    return {
        "status": "success",
        "message": "Akun berhasil didaftarkan.",
        "data": {
            "id": user_id,
            "email": payload.email,
            "name": payload.name,
            "role": payload.role
        }
    }
