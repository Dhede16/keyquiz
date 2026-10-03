"""Logika Penilaian Esai Hibrida: Kemiripan Makna + Rubrik LLM + Kelengkapan."""
from app.services import embedding_service as es
from app.services.llm_service import evaluasi_llm

# Bobot penilaian (total 100%)
BOBOT_SIMILARITY = 0.60
BOBOT_RUBRIK = 0.30
BOBOT_KELENGKAPAN = 0.10

# Threshold similarity (skala 0-100)
# < 30  -> nilai 0
# >= 90 -> nilai 100
# 30-90 -> dihitung dengan bobot (LLM dipanggil hanya di rentang ini)
SIMILARITY_MIN = 30
SIMILARITY_MAX = 90


def tentukan_kategori(nilai: float) -> str:
    """Konversi nilai numerik ke kategori predikat."""
    if nilai >= 90:
        return "Sangat Baik"
    if nilai >= 80:
        return "Baik"
    if nilai >= 70:
        return "Cukup"
    if nilai >= 60:
        return "Kurang"
    return "Sangat Kurang"


def nilai_esai(id_detail: str, id_soal: str, jawaban_teks: str) -> dict:
    """Menilai jawaban esai mahasiswa secara otomatis."""
    jawaban_teks = jawaban_teks.strip()

    if not jawaban_teks:
        return {
            "nilai_ai": 0.0,
            "kategori": tentukan_kategori(0),
            "status": "Jawaban kosong",
        }

    # 1. Hitung Semantic Similarity via ChromaDB
    vektor = es.buat_embedding(jawaban_teks)
    data = es.cari_kunci(vektor, id_soal)
    similarity = data["similarity"]
    es.simpan_jawaban(id_detail, id_soal, jawaban_teks, vektor)

    hasil = {"similarity": round(similarity, 2)}

    # 2. Tentukan nilai akhir berdasarkan rentang threshold
    if similarity < SIMILARITY_MIN:
        nilai = 0.0
        hasil["status"] = "Similarity terlalu rendah, nilai otomatis 0"

    elif similarity >= SIMILARITY_MAX:
        nilai = 100.0
        hasil["status"] = "Similarity sangat tinggi, nilai otomatis 100"

    else:
        # Rentang menengah: Evaluasi rubrik kriteria dan kelengkapan oleh LLM
        llm = evaluasi_llm(data["soal"], data["kunci"], jawaban_teks, data["rubrik"])
        nilai = round(
            similarity * BOBOT_SIMILARITY
            + llm["rubric_score"] * BOBOT_RUBRIK
            + llm["completeness_score"] * BOBOT_KELENGKAPAN,
            2,
        )
        hasil["status"] = "Dihitung dengan bobot"
        hasil["rubric_score"] = round(llm["rubric_score"], 2)
        hasil["completeness_score"] = llm["completeness_score"]
        hasil["rubric_results"] = llm["rubric_results"]
        hasil["alasan_ai"] = llm["overall_reason"]

    hasil["nilai_ai"] = nilai
    hasil["kategori"] = tentukan_kategori(nilai)
    return hasil
