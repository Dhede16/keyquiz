"""Pengujian Mandiri Scan Jawaban Kertas KeyQuiz."""
import json
import sys
import os
from app.services import scan_service as ss

if __name__ == "__main__":
    jalur_foto = sys.argv[1] if len(sys.argv) > 1 else os.path.join("foto-testing-scan", "foto_soal_pilihan_ganda.jpg")
    jenis = sys.argv[2] if len(sys.argv) > 2 else "pilihan_ganda"

    if not os.path.exists(jalur_foto):
        print(f"File '{jalur_foto}' tidak ditemukan.")
        sys.exit(1)

    with open(jalur_foto, "rb") as f:
        data = f.read()

    hasil = ss.baca_foto(data, jenis)
    print("=== HASIL BACA FOTO ===")
    print(json.dumps(hasil, indent=2, ensure_ascii=False))

    if jenis == "pilihan_ganda":
        kunci_pg = {
            "1": "a", "2": "b", "3": "a", "4": "c", "5": "a",
            "6": "d", "7": "b", "8": "c", "9": "a", "10": "b",
            "11": "a", "12": "d", "13": "c"
        }
        rekap = ss.nilai_pilihan_ganda(hasil, kunci_pg, total_soal=13)
        print("\n=== REKAP PENILAIAN ===")
        print(json.dumps(rekap, indent=2, ensure_ascii=False))

