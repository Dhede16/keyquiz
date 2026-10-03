"""Client AI Groq untuk inferensi LLM dan Vision AI."""
import json
import re
from typing import Any
from groq import Groq
from app.config import GROQ_API_KEY, NAMA_MODEL_VISION, NAMA_MODEL_LLM

_groq_client = None


def get_groq_client() -> Groq:
    """Mengembalikan singleton instance Groq client."""
    global _groq_client
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY belum dikonfigurasi di environment atau file .env")
    if _groq_client is None:
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


def panggil_ai_json(messages: list[dict], model: str = None) -> Any:
    """Kirim messages ke Groq dan ekstrak response JSON."""
    client = get_groq_client()
    target_model = model or NAMA_MODEL_VISION

    respons = client.chat.completions.create(
        model=target_model,
        messages=messages,
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    raw = respons.choices[0].message.content or ""

    # Bersihkan markdown codeblock ```json jika ada
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    return json.loads(clean)
