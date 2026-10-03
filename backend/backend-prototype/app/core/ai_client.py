"""Core AI Client for KeyQuiz."""
import json
from groq import Groq
from app.config import GROQ_API_KEY, NAMA_MODEL_VISION

# Reasoning effort: "none", "default", "low", "medium", "high"
REASONING_EFFORT = "default"

groq_client = Groq(api_key=GROQ_API_KEY)


def ambil_json(teks: str) -> dict:
    """Ambil objek JSON dari balasan model (abaikan teks di luar kurung kurawal)."""
    awal = teks.find("{")
    akhir = teks.rfind("}")
    return json.loads(teks[awal:akhir + 1])


def panggil_ai_json(messages: list, model: str = NAMA_MODEL_VISION) -> dict:
    """Kirim pesan (bisa teks atau gambar) ke model Groq dan kembalikan hasil JSON."""
    respons = groq_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        max_completion_tokens=4096,
        reasoning_effort=REASONING_EFFORT,
        reasoning_format="hidden",
        response_format={"type": "json_object"},
    )
    return ambil_json(respons.choices[0].message.content)
