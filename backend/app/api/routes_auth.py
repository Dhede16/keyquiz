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
            "message": "User berhasil didaftarkan langsung ke Supabase Auth dan tabel profiles.",
            "data": {
                "id": user_id,
                "email": payload.email,
                "name": payload.name,
                "role": payload.role
            }
        }
    except Exception as e:
        error_msg = str(e)
        code = getattr(e, "code", "") or ""
        # Jika user sudah pernah terdaftar di auth.users (misal profil belum sinkron/hilang),
        # cari user tersebut, perbarui password/metadata, dan pastikan masuk ke tabel profiles
        is_already_registered = (
            code == "email_exists"
            or ("already" in error_msg.lower() and "registered" in error_msg.lower())
            or ("already" in error_msg.lower() and "exists" in error_msg.lower())
            or "user already exists" in error_msg.lower()
        )
        if is_already_registered:
            try:
                res_users = admin.auth.admin.list_users()
                users_list = getattr(res_users, "users", res_users) if hasattr(res_users, "users") else res_users
                existing_user = None
                if isinstance(users_list, list):
                    for u in users_list:
                        u_email = getattr(u, "email", "") or (u.get("email") if isinstance(u, dict) else "")
                        if u_email.strip().lower() == payload.email.strip().lower():
                            existing_user = u
                            break

                if existing_user:
                    u_id = getattr(existing_user, "id", None) or (existing_user.get("id") if isinstance(existing_user, dict) else None)
                    if u_id:
                        # Update user password & metadata
                        admin.auth.admin.update_user_by_id(u_id, {
                            "password": payload.password,
                            "email_confirm": True,
                            "user_metadata": {
                                "name": payload.name.strip(),
                                "role": payload.role,
                                "password": payload.password
                            }
                        })
                        # Pastikan tabel profiles terisi
                        admin.table("profiles").upsert({
                            "id": u_id,
                            "email": payload.email.strip(),
                            "name": payload.name.strip(),
                            "role": payload.role,
                            "password": payload.password
                        }).execute()

                        return {
                            "status": "success",
                            "message": "User sudah terdaftar di auth, data berhasil disinkronkan ke tabel profiles.",
                            "data": {
                                "id": u_id,
                                "email": payload.email,
                                "name": payload.name,
                                "role": payload.role
                            }
                        }
            except Exception as sync_err:
                print(f"[routes_auth] Gagal sinkronisasi user lama: {sync_err}")

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email tersebut sudah terdaftar di Supabase Auth. Silakan gunakan tombol Masuk untuk login."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gagal mendaftarkan user: {error_msg}"
        )
