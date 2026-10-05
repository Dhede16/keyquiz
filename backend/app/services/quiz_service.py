"""Service Pembuatan Soal & Kuis Otomatis Berbasis AI (Qwen/Llama LLM)."""
import json
from typing import Literal, TypedDict

from app.core.ai_client import get_groq_client
from app.config import NAMA_MODEL_LLM

SYSTEM_QUIZ_PROMPT = """
Anda adalah asisten AI pembuat soal dan evaluasi akademik profesional.
Tugas Anda adalah membuat paket soal ujian (pilihan ganda dan/atau esai) beserta kunci jawaban dan rubrik penilaian yang komprehensif berdasarkan instruksi pengajar.
Untuk kunci jawaban esai, tulis jawaban singkat, padat, dan jelas: maksimal 1–3 kalimat atau sekitar 50 kata. Cantumkan hanya konsep, fakta, istilah, atau langkah inti yang diperlukan agar jawaban tetap tepat dan mewakili pertanyaan. Hindari pengulangan dan uraian tambahan, tetapi jangan hilangkan syarat atau poin penting; jika pertanyaan meminta beberapa hal, jawab semuanya secara ringkas.
Pastikan kunci jawaban akurat dan langsung menjawab pertanyaan; jangan mengarang informasi yang tidak didukung konteks.
Pastikan total nilai bobot seluruh soal tepat 100 poin.
"""


class ChatMessage(TypedDict):
    role: Literal["user", "assistant"]
    content: str


def generate_quiz_ai(
    prompt_text: str,
    conversation_history: list[ChatMessage] | None = None,
) -> dict:
    """Generate soal beserta kunci dan rubrik berdasarkan instruksi bebas dosen."""
    client = get_groq_client()

    user_prompt = f"""
Buatkan paket soal ujian berdasarkan instruksi berikut (ikuti PERSIS jumlah dan tipe soal yang diminta):
"{prompt_text}"

Jika instruksi tidak menyebut jumlah/tipe soal tertentu, tentukan sendiri yang paling sesuai.
Atur nilai "bobot" tiap soal sehingga jumlah seluruhnya tepat 100 poin.

Keluarkan HANYA JSON dengan struktur:
{{
  "judul": "string judul kuis/tugas",
  "deskripsi": "string penjelasan singkat topik",
  "soal": [
    {{
      "nomor": 1,
      "tipe": "multiple_choice",
      "pertanyaan": "teks pertanyaan pilihan ganda",
      "opsi": [
        {{"huruf": "A", "teks": "teks opsi A"}},
        {{"huruf": "B", "teks": "teks opsi B"}},
        {{"huruf": "C", "teks": "teks opsi C"}},
        {{"huruf": "D", "teks": "teks opsi D"}}
      ],
      "kunci_jawaban": "A",
      "bobot": 10
    }},
    {{
      "nomor": 2,
      "tipe": "essay",
      "pertanyaan": "teks pertanyaan esai",
      "kunci_jawaban": "jawaban acuan esai yang singkat, tepat, dan mencakup poin inti",
      "rubrik": [
        "Kriteria 1: penjelasan poin utama",
        "Kriteria 2: penjelasan mekanisme",
        "Kriteria 3: contoh atau kesimpulan"
      ],
      "bobot": 20
    }}
  ]
}}
"""

    respons = client.chat.completions.create(
        model=NAMA_MODEL_LLM,
        messages=[
            {"role": "system", "content": SYSTEM_QUIZ_PROMPT},
            *(conversation_history or []),
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    raw = respons.choices[0].message.content
    return json.loads(raw)
