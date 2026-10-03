"""Logika Penilaian Esai Hibrida: Kemiripan Makna + Rubrik LLM + Kelengkapan."""
import json
from app.services import embedding_service as es
from app.core.ai_client import get_groq_client
from app.config import NAMA_MODEL_LLM

BOBOT_SIMILARITY = 0.60
BOBOT_RUBRIK = 0.30
BOBOT_KELENGKAPAN = 0.10

SIMILARITY_MIN = 30.0
SIMILARITY_MAX = 90.0

SYSTEM_PROMPT = """
Anda adalah evaluator jawaban esai akademik profesional.
Nilai secara objektif berdasarkan soal, kunci jawaban, rubrik kriteria, dan KESESUAIAN MAKNA jawaban siswa.
Jangan menganggap jawaban benar hanya karena memuat beberapa kata yang sama dengan kunci jika maknanya tidak sesuai.
"""


def tentukan_kategori(nilai: float) -> str:
    """Konversi skor numerik ke kategori predikat mutu."""
    if nilai >= 90:
        return "Sangat Baik"
    if nilai >= 80:
        return "Baik"
    if nilai >= 70:
        return "Cukup"
    if nilai >= 60:
        return "Kurang"
    return "Sangat Kurang"


def evaluasi_rubrik_llm(soal: str, kunci: str, jawaban: str, rubrik: list[str]) -> dict:
    """Evaluasi rubrik kriteria dan kelengkapan menggunakan LLM via Groq."""
    client = get_groq_client()
    teks_rubrik = "\n".join(f"{i + 1}. {r}" for i, r in enumerate(rubrik)) if rubrik else "- Kesesuaian pemahaman konsep umum"

    prompt = f"""
Evaluasi jawaban siswa berikut berdasarkan soal, kunci jawaban acuan, dan rubrik penilaian.
Penilaian WAJIB berfokus pada KESESUAIAN MAKNA (semantik), bukan kesamaan kata secara harfiah.

Jika jawaban siswa sama sekali tidak menjawab pertanyaan, asal-asalan, atau menyatakan tidak tahu, maka semua kriteria rubrik harus bernilai false dan completeness_score = 0.

SOAL:
{soal}

KUNCI JAWABAN:
{kunci}

RUBRIK PENILAIAN:
{teks_rubrik}

JAWABAN SISWA:
{jawaban}

Keluarkan HANYA JSON dengan struktur:
{{
  "rubric_results": [
    {{"criterion": "string nama kriteria", "fulfilled": true/false, "reason": "alasan singkat"}}
  ],
  "completeness_score": 0-100 (angka kelengkapan informasi),
  "overall_reason": "penjelasan evaluasi keseluruhan secara ringkas"
}}
"""

    respons = client.chat.completions.create(
        model=NAMA_MODEL_LLM,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    raw = respons.choices[0].message.content
    hasil = json.loads(raw)

    rubric_results = hasil.get("rubric_results", [])
    if rubrik and rubric_results:
        terpenuhi = sum(1 for r in rubric_results if r.get("fulfilled"))
        rubric_score = (terpenuhi / len(rubric_results)) * 100
    else:
        rubric_score = 100.0 if not rubrik else 0.0

    completeness_score = max(0.0, min(100.0, float(hasil.get("completeness_score", 50.0))))

    return {
        "rubric_results": rubric_results,
        "rubric_score": rubric_score,
        "completeness_score": completeness_score,
        "overall_reason": hasil.get("overall_reason", ""),
    }


def nilai_esai(id_detail: str, id_soal: str, jawaban_teks: str) -> dict:
    """Menilai jawaban esai mahasiswa secara otomatis dengan metode hibrida."""
    jawaban_teks = (jawaban_teks or "").strip()

    if not jawaban_teks:
        return {
            "id_detail": id_detail,
            "id_soal": id_soal,
            "similarity": 0.0,
            "nilai_ai": 0.0,
            "kategori": tentukan_kategori(0.0),
            "status": "Jawaban kosong",
        }

    # 1. Hitung Semantic Similarity
    vektor = es.buat_embedding(jawaban_teks)
    data_kunci = es.cari_kunci(vektor, id_soal)
    similarity = data_kunci["similarity"]
    es.simpan_jawaban(id_detail, id_soal, jawaban_teks, vektor)

    hasil = {
        "id_detail": id_detail,
        "id_soal": id_soal,
        "similarity": round(similarity, 2),
    }

    # 2. Terapkan threshold rule
    if similarity < SIMILARITY_MIN:
        nilai = 0.0
        hasil["status"] = "Similarity terlalu rendah, nilai otomatis 0"
        hasil["rubric_results"] = []
        hasil["rubric_score"] = 0.0
        hasil["completeness_score"] = 0.0
        hasil["alasan_ai"] = "Jawaban tidak sesuai dengan kunci jawaban atau di luar topik."

    elif similarity >= SIMILARITY_MAX:
        nilai = 100.0
        hasil["status"] = "Similarity sangat tinggi, nilai otomatis 100"
        hasil["rubric_results"] = []
        hasil["rubric_score"] = 100.0
        hasil["completeness_score"] = 100.0
        hasil["alasan_ai"] = "Jawaban sangat selaras dan memenuhi esensi kunci jawaban secara sempurna."

    else:
        # Rentang menengah: Evaluasi Rubrik & Kelengkapan oleh LLM
        llm = evaluasi_rubrik_llm(
            data_kunci["soal"],
            data_kunci["kunci"],
            jawaban_teks,
            data_kunci["rubrik"],
        )
        nilai = round(
            similarity * BOBOT_SIMILARITY
            + llm["rubric_score"] * BOBOT_RUBRIK
            + llm["completeness_score"] * BOBOT_KELENGKAPAN,
            2,
        )
        hasil["status"] = "Dihitung dengan bobot hibrida"
        hasil["rubric_score"] = round(llm["rubric_score"], 2)
        hasil["completeness_score"] = llm["completeness_score"]
        hasil["rubric_results"] = llm["rubric_results"]
        hasil["alasan_ai"] = llm["overall_reason"]

    hasil["nilai_ai"] = nilai
    hasil["kategori"] = tentukan_kategori(nilai)
    return hasil
