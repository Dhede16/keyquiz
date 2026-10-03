"""KeyQuiz Backend - Entrypoint & Prototype Testing Suite.

Untuk menjalankan pengujian prototype otomatis:
    python main.py

Untuk menjalankan REST API server:
    uvicorn main:app --reload
"""
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.services import embedding_service as es
from app.services import scan_service as ss
from app.services.essay_service import nilai_esai

app = FastAPI(
    title="KeyQuiz API",
    description="Sistem Penilaian Esai Berbasis AI dan Pemindaian Lembar Jawaban Kertas",
    version="1.0.0",
)

# CORS Middleware agar siap diakses frontend Vue.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrasi Router
app.include_router(api_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "service": "KeyQuiz Backend API",
        "docs": "/docs",
    }


def jalankan_pengujian_prototype():
    """Menjalankan alur lengkap pengujian Penilaian Esai dan Scan Vision."""
    import os

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 65)
    print(">>> KEYQUIZ BACKEND PROTOTYPE - TESTING SUITE <<<")
    print("=" * 65)

    # 1. PENGUJIAN PENILAIAN ESAI
    print("\n" + "=" * 65)
    print("[1/2] PENGUJIAN PENILAIAN ESAI OTOMATIS (AI + SEMANTIC SIMILARITY)")
    print("=" * 65)

    id_soal = "soal-demo-1"
    id_kunci = "kunci-demo-1"
    soal = "Jelaskan apa yang dimaksud dengan fotosintesis."
    kunci = "Fotosintesis adalah proses tumbuhan membuat makanan sendiri dengan menggunakan energi cahaya matahari."
    rubrik = [
        "Menjelaskan bahwa fotosintesis merupakan proses pembuatan makanan",
        "Menyebutkan bahwa proses terjadi pada tumbuhan",
        "Menyebutkan bahwa cahaya matahari digunakan sebagai sumber energi",
    ]

    print(f"Soal   : {soal}")
    print(f"Kunci  : {kunci}")
    print("Rubrik :")
    for i, r in enumerate(rubrik, 1):
        print(f"   {i}. {r}")

    print("\nMenyimpan kunci jawaban ke ChromaDB...")
    es.simpan_kunci(id_kunci, id_soal, soal, kunci, rubrik)
    print("[OK] Kunci jawaban berhasil disimpan.")

    sampel_jawaban = [
        (
            "Jawaban Lengkap (Mirip Kunci)",
            "Fotosintesis adalah proses tumbuhan membuat makanan sendiri dengan energi cahaya matahari.",
        ),
        (
            "Jawaban Sebagian (Rentang Menengah)",
            "Fotosintesis adalah proses pada tumbuhan yang memakai cahaya.",
        ),
        (
            "Jawaban Tidak Tahu / Asal",
            "Saya tidak tahu jawabannya dan tidak belajar.",
        ),
    ]

    for label, teks in sampel_jawaban:
        print(f"\n--- Menguji: {label} ---")
        print(f"Jawaban: \"{teks}\"")
        hasil = nilai_esai(f"detail-{label.replace(' ', '_')}", id_soal, teks)
        print(f"  * Kemiripan Semantik (Similarity) : {hasil.get('similarity')}%")
        print(f"  * Status Penilaian                : {hasil.get('status')}")
        if "rubric_score" in hasil:
            print(f"  * Skor Rubrik                     : {hasil.get('rubric_score')}%")
            print(f"  * Skor Kelengkapan                : {hasil.get('completeness_score')}%")
            print(f"  * Evaluasi Rubrik Detail          :")
            for item in hasil.get("rubric_results", []):
                status_icon = "[TERPENUHI]" if item["fulfilled"] else "[TIDAK]"
                print(f"      {status_icon} {item['criterion']} -> {item['reason']}")
            print(f"  * Alasan Evaluasi AI              : {hasil.get('alasan_ai')}")
        print(f"  >>> NILAI AKHIR AI                : {hasil.get('nilai_ai')} ({hasil.get('kategori')})")

    # 2. PENGUJIAN SCAN JAWABAN KERTAS
    print("\n" + "=" * 65)
    print("[2/2] PENGUJIAN SCAN JAWABAN KERTAS (VISION AI)")
    print("=" * 65)

    jalur_foto = os.path.join("foto-testing-scan", "foto_soal_pilihan_ganda.jpg")
    if not os.path.exists(jalur_foto):
        print(f"[PERINGATAN] File foto '{jalur_foto}' tidak ditemukan.")
    else:
        print(f"Membaca lembar jawaban dari: {jalur_foto}")
        with open(jalur_foto, "rb") as f:
            data_gambar = f.read()

        print("Memproses gambar dengan Qwen Vision...")
        terbaca = ss.baca_foto(data_gambar, "pilihan_ganda")
        print(f"[OK] Berhasil membaca {len(terbaca)} nomor soal.")

        # Kunci jawaban lengkap untuk seluruh 13 nomor soal pada lembar ujian
        kunci_pg = {
            "1": "a", "2": "b", "3": "a", "4": "c", "5": "a",
            "6": "d", "7": "b", "8": "c", "9": "a", "10": "b",
            "11": "a", "12": "d", "13": "c"
        }
        total_soal_ujian = 13
        hasil_pg = ss.nilai_pilihan_ganda(terbaca, kunci_pg, total_soal=total_soal_ujian)

        print(f"\n--- Rincian Status Per Nomor (Total: {total_soal_ujian} Soal) ---")
        for d in hasil_pg["detail"]:
            jwb = d["jawaban"].upper() if d["jawaban"] else "(tidak dijawab)"
            knc = d["kunci"].upper() if d["kunci"] else "-"
            status_tag = f"[{d['status'].upper()}]"
            print(f"   Nomor {d['nomor']:2d} | Jawaban: {jwb:16s} | Kunci: {knc} | Status: {status_tag}")

        print("\n--- Rekapitulasi Nilai Ujian Pilihan Ganda ---")
        print(f"   * Jumlah Total Soal : {hasil_pg['total_soal']}")
        print(f"   * Jawaban Benar     : {hasil_pg['benar']} (Mendapat poin)")
        print(f"   * Jawaban Salah     : {hasil_pg['salah']} (0 poin)")
        print(f"   * Tidak Terjawab    : {hasil_pg['kosong']} (0 poin)")
        print(f"   * Formula Nilai     : ({hasil_pg['benar']} / {hasil_pg['total_soal']}) * 100")
        print(f"   >>> NILAI AKHIR PG  : {hasil_pg['nilai']}%")

    print("\n" + "=" * 65)
    print("[SELESAI] SEMUA PENGUJIAN BERHASIL DIJALANKAN.")
    print("Catatan: Untuk menjalankan API server FastAPI, jalankan:")
    print("         uvicorn main:app --reload")
    print("=" * 65)


if __name__ == "__main__":
    jalankan_pengujian_prototype()
