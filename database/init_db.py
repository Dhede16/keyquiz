"""Script otomatis untuk inisialisasi tabel Supabase PostgreSQL menggunakan schema.sql."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env dari root project
root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def main():
    print("=" * 60)
    print(">>> KEYQUIZ - SUPABASE DATABASE INITIALIZER <<<")
    print("=" * 60)

    if not DATABASE_URL or "your-password" in DATABASE_URL or "your-project-ref" in DATABASE_URL:
        print("\n[PERINGATAN] DATABASE_URL belum dikonfigurasi dengan benar di file .env")
        print("Silakan isi DATABASE_URL di file .env dengan connection string Supabase Anda:")
        print("Contoh: postgresql://postgres.xxxx:mypassword@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require")
        print("\nAtau Anda dapat langsung menyalin isi file 'database/schema.sql' ke SQL Editor di Supabase Dashboard.")
        return

    if not SCHEMA_PATH.exists():
        print(f"[ERROR] File schema '{SCHEMA_PATH}' tidak ditemukan.")
        return

    print(f"Membaca skema dari: {SCHEMA_PATH.name}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql_content = f.read()

    print("Mencoba menghubungkan ke Supabase PostgreSQL...")
    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(sql_content)
        conn.close()
        print("[SUKSES] Semua tabel, trigger, dan RLS policy berhasil dibuat di Supabase!")
    except ImportError:
        print("\n[INFO] Driver 'psycopg2' belum terinstall.")
        print("Mencoba menggunakan sqlalchemy/asyncpg atau alternatif...")
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(DATABASE_URL)
            with engine.connect() as connection:
                connection.execute(text(sql_content))
                connection.commit()
            print("[SUKSES] Semua tabel berhasil dibuat via SQLAlchemy!")
        except Exception as ex:
            print(f"[GAGAL] Error saat eksekusi: {ex}")
            print("\nTips: Anda dapat menjalankan 'pip install psycopg2-binary' atau langsung paste isi 'database/schema.sql' ke SQL Editor Supabase.")
    except Exception as e:
        print(f"[GAGAL] Terjadi kesalahan saat mengeksekusi SQL: {e}")


if __name__ == "__main__":
    main()
