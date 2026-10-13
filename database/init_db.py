"""Apply the base Supabase schema and all ordered SQL migrations."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "")
DATABASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = DATABASE_DIR / "schema.sql"
MIGRATIONS_DIR = DATABASE_DIR / "migrations"


def main() -> None:
    if not DATABASE_URL or any(
        placeholder in DATABASE_URL
        for placeholder in ("your-password", "your-project-ref")
    ):
        print("[ERROR] DATABASE_URL belum dikonfigurasi.", file=sys.stderr)
        raise SystemExit(1)

    if not SCHEMA_PATH.is_file():
        print(f"[ERROR] File schema '{SCHEMA_PATH}' tidak ditemukan.", file=sys.stderr)
        raise SystemExit(1)

    try:
        import psycopg2
    except ImportError:
        print(
            "[ERROR] psycopg2 belum terpasang. Jalankan pip install -r backend/requirements.txt.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    sql_paths = [
        ("000_schema", SCHEMA_PATH),
        *(
            (path.stem, path)
            for path in sorted(MIGRATIONS_DIR.glob("*.sql"))
        ),
    ]
    connection = None
    current_path = SCHEMA_PATH

    try:
        connection = psycopg2.connect(DATABASE_URL)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS public.keyquiz_schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                "REVOKE ALL ON TABLE public.keyquiz_schema_migrations "
                "FROM anon, authenticated"
            )
        connection.commit()

        for version, current_path in sql_paths:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM public.keyquiz_schema_migrations "
                    "WHERE version = %s",
                    (version,),
                )
                already_applied = cursor.fetchone() is not None
            connection.commit()
            if already_applied:
                print(
                    "[LEWATI] Sudah diterapkan:",
                    current_path.relative_to(DATABASE_DIR),
                )
                continue

            with current_path.open("r", encoding="utf-8") as sql_file:
                sql_content = sql_file.read()
            with connection.cursor() as cursor:
                cursor.execute(sql_content)
                cursor.execute(
                    "INSERT INTO public.keyquiz_schema_migrations (version) "
                    "VALUES (%s)",
                    (version,),
                )
            connection.commit()
            print(
                "[SUKSES] Diterapkan:",
                current_path.relative_to(DATABASE_DIR),
            )
    except Exception as exc:
        if connection is not None:
            connection.rollback()
        print(
            f"[GAGAL] Database initialization berhenti pada {current_path.name}: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    finally:
        if connection is not None:
            connection.close()

    print("[SUKSES] Schema dan semua migrasi berhasil diterapkan.")


if __name__ == "__main__":
    main()
