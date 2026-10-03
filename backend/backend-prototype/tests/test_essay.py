"""Pengujian Mandiri Penilaian Esai KeyQuiz."""
import json
from app.services import embedding_service as es
from app.services.essay_service import nilai_esai

SOAL = "Jelaskan apa yang dimaksud dengan fotosintesis."
KUNCI = "Fotosintesis adalah proses tumbuhan membuat makanan sendiri dengan menggunakan energi cahaya matahari."
RUBRIK = [
    "Menjelaskan bahwa fotosintesis merupakan proses pembuatan makanan",
    "Menyebutkan bahwa proses terjadi pada tumbuhan",
    "Menyebutkan bahwa cahaya matahari digunakan sebagai sumber energi",
]

if __name__ == "__main__":
    es.simpan_kunci("kunci-test-1", "soal-test-1", SOAL, KUNCI, RUBRIK)

    contoh_jawaban = {
        "mirip kunci": "Fotosintesis adalah proses tumbuhan membuat makanan sendiri dengan energi cahaya matahari.",
        "sebagian": "Fotosintesis adalah proses pada tumbuhan yang memakai cahaya.",
        "tidak tahu": "Saya tidak tahu jawabannya.",
    }

    for nama, jawaban in contoh_jawaban.items():
        hasil = nilai_esai(f"detail-{nama}", "soal-test-1", jawaban)
        print(f"\n=== {nama.upper()} ===")
        print(json.dumps(hasil, indent=2, ensure_ascii=False))
