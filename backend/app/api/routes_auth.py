"""Router Autentikasi Backend untuk bypass rate limit dan pembuatan user langsung."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.core.supabase import get_supabase_admin

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterAdminRequest(BaseModel):
    email: str
    password: str
    name: str
    role: str = "student"


@router.post("/register-admin")
def register_user_admin(payload: RegisterAdminRequest):
    """Mendaftarkan akun baru secara langsung via Supabase Admin API.
    
    Fitur ini secara otomatis mem-bypass pengiriman email dan email rate limit
    dengan menandai email_confirm = True.
    """
    admin = get_supabase_admin()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin client Supabase belum terkonfigurasi di backend."
        )

    try:
        # Create user via Supabase Auth Admin API with auto-confirmed email
        res = admin.auth.admin.create_user({
            "email": payload.email.strip(),
            "password": payload.password,
            "email_confirm": True,
            "user_metadata": {
                "name": payload.name.strip(),
                "role": payload.role,
                "password": payload.password
            }
        })

        user_id = res.user.id if res.user else None

        # Ensure profile record is inserted/updated
        if user_id:
            admin.table("profiles").upsert({
                "id": user_id,
                "email": payload.email.strip(),
                "name": payload.name.strip(),
                "role": payload.role,
                "password": payload.password
            }).execute()

        return {
            "status": "success",
            "message": "User berhasil didaftarkan langsung tanpa kendala email rate limit.",
            "data": {
                "id": user_id,
                "email": payload.email,
                "name": payload.name,
                "role": payload.role
            }
        }
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email tersebut sudah terdaftar. Silakan gunakan email lain atau langsung masuk."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gagal mendaftarkan user: {error_msg}"
        )
