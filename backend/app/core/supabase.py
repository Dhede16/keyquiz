"""Client Supabase Helper untuk operasi Database dan Auth di Backend."""
from typing import Optional
from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY

_supabase_client: Optional[Client] = None
_admin_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """Mengembalikan standard Supabase Client dengan anon key."""
    global _supabase_client
    if not _supabase_client and SUPABASE_URL and SUPABASE_ANON_KEY:
        try:
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        except Exception as e:
            print(f"[WARN] Gagal inisialisasi Supabase client: {e}")
    return _supabase_client


def get_supabase_admin() -> Optional[Client]:
    """Mengembalikan Admin Supabase Client dengan Service Role Key untuk bypass RLS pada backend sync."""
    global _admin_client
    key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
    if not _admin_client and SUPABASE_URL and key:
        try:
            _admin_client = create_client(SUPABASE_URL, key)
        except Exception as e:
            print(f"[WARN] Gagal inisialisasi Supabase admin client: {e}")
    return _admin_client
