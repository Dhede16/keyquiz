"""
Script Reset Database Manual - KeyQuiz Backend
=============================================================================
Fungsi:
Membersihkan (truncate/reset) seluruh data tabel di database PostgreSQL / Supabase,
membersihkan data users (auth.users), serta mereset vector database (ChromaDB)
agar backend kembali ke kondisi awal (fresh start) untuk keperluan Quality Check & Testing.

Cara Menjalankan:
    cd backend
    python reset_db.py
    # atau jika ingin melewati konfirmasi:
    python reset_db.py --yes
=============================================================================
"""

import os
import sys
import shutil
import argparse
from pathlib import Path

# Pastikan root backend ada di sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app.config import (
    DATABASE_URL,
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_ANON_KEY,
    CHROMA_DB_PATH,
)
from app.core.supabase import get_supabase_admin

# Urutan tabel relasional (dari child ke parent untuk penghapusan aman)
TABLES = [
    "detail_jawaban",
    "jawaban_mahasiswa",
    "kunci_jawaban_essay",
    "opsi_jawaban",
    "soal",
    "tugas",
    "anggota_kelas",
    "kelas",
    "profiles",
]


def reset_via_psycopg2(database_url: str) -> bool:
    """Mereset seluruh tabel database melalui koneksi direct PostgreSQL (psycopg2)."""
    try:
        import psycopg2
    except ImportError:
        print("[-] Modul psycopg2 belum terpasang. Mencoba metode alternatif...")
        return False

    print("\n[+] Menghubungkan ke PostgreSQL melalui DATABASE_URL...")
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()

        # 1. Truncate semua public tables sekaligus dengan CASCADE
        tables_str = ", ".join([f"public.{t}" for t in TABLES])
        print(f"[+] Menjalankan TRUNCATE CASCADE pada tabel public:")
        for t in TABLES:
            print(f"    - public.{t}")
        
        cursor.execute(f"TRUNCATE TABLE {tables_str} RESTART IDENTITY CASCADE;")
        print("[V] Seluruh tabel public berhasil di-truncate.")

        # 2. Reset auth.users jika diizinkan (Supabase Postgres)
        try:
            cursor.execute("TRUNCATE TABLE auth.users RESTART IDENTITY CASCADE;")
            print("[V] Tabel auth.users berhasil di-truncate (Supabase Auth bersih).")
        except Exception as auth_err:
            print(f"[!] Info: Tidak dapat me-reset auth.users via SQL direct: {auth_err}")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[-] Gagal me-reset database via psycopg2: {e}")
        return False


def reset_via_supabase_api() -> bool:
    """Mereset data melalui Supabase Admin REST Client sebagai fallback jika direct PG gagal."""
    print("\n[+] Menggunakan Supabase Admin API client...")
    client = get_supabase_admin()
    if not client:
        print("[-] Supabase Admin Client tidak tersedia. Periksa SUPABASE_URL & SUPABASE_SERVICE_ROLE_KEY di .env")
        return False

    # 1. Hapus isi tabel satu per satu dari child ke parent
    for table in TABLES:
        try:
            print(f"    - Menghapus data tabel '{table}'...")
            # Menggunakan filter neq id default uuid kosong untuk menghapus semua baris
            client.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            print(f"      [V] Tabel '{table}' dibersihkan.")
        except Exception as e:
            print(f"      [!] Gagal membersihkan '{table}': {e}")

    # 2. Bersihkan Supabase Auth Users
    try:
        print("[+] Membersihkan Auth Users dari Supabase...")
        res = client.auth.admin.list_users()
        users = getattr(res, "users", res) if hasattr(res, "users") else res
        if isinstance(users, list):
            for user in users:
                user_id = getattr(user, "id", None) or user.get("id")
                if user_id:
                    client.auth.admin.delete_user(user_id)
            print(f"      [V] {len(users)} pengguna auth berhasil dihapus.")
    except Exception as e:
        print(f"      [!] Gagal membersihkan Supabase Auth Users: {e}")

    return True


def reset_chromadb() -> None:
    """Mereset koleksi dan folder penyimpanan ChromaDB."""
    print("\n[+] Mereset ChromaDB (Vector Database)...")
    
    # Coba reset lewat chromadb client jika modul ada
    try:
        import chromadb
        resolved_path = str(Path(CHROMA_DB_PATH).resolve())
        if os.path.exists(resolved_path):
            client = chromadb.PersistentClient(path=resolved_path)
            for collection in client.list_collections():
                col_name = collection.name if hasattr(collection, "name") else collection
                client.delete_collection(col_name)
                print(f"    [V] Koleksi ChromaDB '{col_name}' dihapus.")
    except Exception as e:
        print(f"    [!] Reset koleksi ChromaDB via API: {e}")

    # Hapus file direktori ChromaDB fisik jika ada
    try:
        chroma_dir = Path(CHROMA_DB_PATH)
        if chroma_dir.is_absolute():
            target_dir = chroma_dir
        else:
            target_dir = BASE_DIR / CHROMA_DB_PATH

        if target_dir.exists() and target_dir.is_dir():
            shutil.rmtree(target_dir, ignore_errors=True)
            print(f"    [V] Direktori fisik '{target_dir}' berhasil dibersihkan.")
    except Exception as e:
        print(f"    [!] Gagal menghapus direktori fisik ChromaDB: {e}")


def main():
    parser = argparse.ArgumentParser(description="Reset semua tabel database KeyQuiz dan ChromaDB.")
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Lewati konfirmasi interaktif (langsung eksekusi reset)",
    )
    args = parser.parse_args()

    print("=" * 65)
    print("   KEYQUIZ - DATABASE & VECTOR DB RESET TOOL (MANUAL RUN)")
    print("=" * 65)
    print("PERINGATAN: Tindakan ini akan MENGHAPUS SEMUA DATA tabel di database!")
    print("Tabel yang akan direset:")
    for t in TABLES:
        print(f" - {t}")
    print(" - auth.users (Supabase Auth)")
    print(" - ChromaDB collections & embeddings")
    print("=" * 65)

    if not args.yes:
        confirm = input("\nApakah Anda yakin ingin melanjutkan reset total? (ketik 'y' / 'yes' untuk lanjut): ").strip().lower()
        if confirm not in ("y", "yes"):
            print("[-] Operasi reset dibatalkan oleh pengguna.")
            sys.exit(0)

    success = False

    # Prioritas 1: Gunakan DATABASE_URL via psycopg2 untuk reset instan & bersih
    if DATABASE_URL:
        success = reset_via_psycopg2(DATABASE_URL)

    # Prioritas 2: Fallback ke Supabase API Client jika psycopg2 gagal/tidak ada DATABASE_URL
    if not success:
        print("\n[!] Mencoba fallback ke Supabase REST API...")
        success = reset_via_supabase_api()

    # Reset Vector DB (ChromaDB)
    reset_chromadb()

    print("\n" + "=" * 65)
    if success:
        print(">>> SUKSES: Database dan Vector DB berhasil direset ke kondisi awal! <<<")
        print("Anda sekarang dapat memulai Quality Check dengan data baru (fresh start).")
    else:
        print(">>> PERHATIAN: Beberapa operasi reset mungkin tidak berhasil dieksekusi. <<<")
        print("Silakan periksa koneksi internet atau environment variable di .env.")
    print("=" * 65)


if __name__ == "__main__":
    main()
