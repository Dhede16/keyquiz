"""Service Evaluasi Rubrik dan Kelengkapan oleh LLM."""
import json
from groq import Groq
from app.config import GROQ_API_KEY, NAMA_MODEL_LLM

groq_client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
Anda adalah evaluator jawaban esai.
Nilai secara objektif berdasarkan soal, kunci jawaban, rubrik, dan MAKNA jawaban.
Jangan menganggap jawaban benar hanya karena memuat beberapa kata yang sama dengan kunci.
"""

SKEMA_JSON = {
    "name": "essay_evaluation",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "rubric_results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "criterion": {"type": "string"},
                        "fulfilled": {"type": "boolean"},
                        "reason": {"type": "string"},
                    },
                    "required": ["criterion", "fulfilled", "reason"],
                    "additionalProperties": False,
                },
            },
            "completeness_score": {"type": "number"},
            "overall_reason": {"type": "string"},
        },
        "required": ["rubric_results", "completeness_score", "overall_reason"],
        "additionalProperties": False,
    },
}


def buat_prompt(soal: str, kunci: str, jawaban: str, rubrik: list[str]) -> str:
    teks_rubrik = "\n".join(f"{i + 1}. {r}" for i, r in enumerate(rubrik))
    return f"""
Evaluasi jawaban siswa berdasarkan soal, kunci jawaban, dan rubrik.
Penilaian harus berdasarkan KESESUAIAN MAKNA, bukan kesamaan kata.

Jika jawaban tidak menjawab pertanyaan, mengatakan tidak tahu, tidak relevan,
atau tidak memberi informasi tentang topik, maka semua rubrik bernilai false.

SOAL:
{soal}

KUNCI JAWABAN:
{kunci}

RUBRIK:
{teks_rubrik}

JAWABAN SISWA:
{jawaban}

ATURAN RUBRIK:
Periksa setiap rubrik secara terpisah.
fulfilled = true jika jawaban benar-benar memenuhi kriteria berdasarkan makna,
fulfilled = false jika informasinya tidak ada atau tidak didukung jawaban.
Berikan alasan singkat untuk setiap rubrik.

ATURAN completeness_score:
0 = tidak ada informasi relevan, 25 = sangat sedikit, 50 = sebagian,
75 = cukup lengkap, 100 = lengkap dan mencakup informasi penting.
"""


def panggil_llm(prompt: str) -> dict:
    """Kirim prompt ke LLM dan kembalikan hasil JSON sesuai skema rubrik."""
    respons = groq_client.chat.completions.create(
        model=NAMA_MODEL_LLM,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_schema", "json_schema": SKEMA_JSON},
    )
    return json.loads(respons.choices[0].message.content)


def evaluasi_llm(soal: str, kunci: str, jawaban: str, rubrik: list[str]) -> dict:
    """Evaluasi rubrik dan kelengkapan jawaban menggunakan LLM."""
    hasil = panggil_llm(buat_prompt(soal, kunci, jawaban, rubrik))

    terpenuhi = sum(1 for r in hasil["rubric_results"] if r["fulfilled"])
    hasil["rubric_score"] = terpenuhi / len(rubrik) * 100 if rubrik else 100.0
    hasil["completeness_score"] = max(0, min(100, float(hasil["completeness_score"])))
    return hasil
