"""Service Pemindaian Lembar Jawaban Kertas dengan Vision AI."""
import base64
import io
from PIL import Image, ImageOps
from app.core.ai_client import panggil_ai_json

PROMPT_PILIHAN_GANDA = """
Foto ini adalah lembar soal pilihan ganda yang sudah dijawab dengan cara menyilang (x) atau melingkari salah satu huruf pilihan (a, b, c, d, atau e).

Tugas Anda: tentukan huruf pilihan yang ditandai siswa untuk SETIAP nomor soal yang ada di lembar.

Aturan:
- Tanda silang/lingkaran bisa menimpa huruf pilihan atau kata di sebelahnya.
- Pada soal dialog/percakapan, abaikan label dialog (seperti A:, B:, X:, Y:), itu bukan opsi jawaban.
- Jika sebuah nomor tidak ada tandanya, isi "pilihan" dengan null.
- Jika ada tanda tetapi Anda ragu pilihan mana yang dimaksud, isi "yakin" dengan false.
- Laporkan hanya apa yang ditandai siswa, jangan menebak jawaban benar.
- Urutkan nomor soal secara kronologis (1, 2, 3, ...).

Balas HANYA dengan JSON valid tanpa teks lain:
{"jawaban": [{"nomor": 1, "pilihan": "a", "yakin": true}, {"nomor": 2, "pilihan": null, "yakin": true}]}
"""

PROMPT_ESAI = """
Foto ini adalah lembar jawaban esai tulisan tangan siswa.

Tugas Anda: salin jawaban siswa untuk SETIAP nomor soal menjadi teks digital.

Aturan:
- Salin apa adanya, jangan memperbaiki ejaan atau melengkapi jawaban.
- Jika ada kata yang tidak terbaca, tulis [tidak terbaca].
- Jika nomor soal tidak dijawab, isi "teks" dengan string kosong "".
- Urutkan nomor soal secara berurutan.

Balas HANYA dengan JSON valid:
{"jawaban": [{"nomor": 1, "teks": "isi jawaban 1"}, {"nomor": 2, "teks": "isi jawaban 2"}]}
"""


def kecilkan_gambar(data: bytes, sisi_maks: int = 1600) -> bytes:
    """Koreksi orientasi EXIF dan optimalkan resolusi foto agar cepat diproses."""
    gambar = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    gambar.thumbnail((sisi_maks, sisi_maks))
    buffer = io.BytesIO()
    gambar.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


def baca_dengan_ai(data_gambar: bytes, prompt: str) -> dict:
    """Kirim foto base64 ke Vision AI dan kembalikan dictionary respons."""
    base64_gambar = base64.b64encode(data_gambar).decode("utf-8")
    return panggil_ai_json([{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_gambar}"}},
        ],
    }])


def bersihkan_pilihan_ganda(data: dict) -> list[dict]:
    """Normalisasi hasil ekstraksi pilihan ganda."""
    hasil = []
    for item in data.get("jawaban", []):
        pilihan = item.get("pilihan")
        pilihan = pilihan.strip().lower() if isinstance(pilihan, str) else None
        if pilihan not in ("a", "b", "c", "d", "e"):
            pilihan = None
        hasil.append({
            "nomor": int(item["nomor"]),
            "pilihan": pilihan,
            "yakin": bool(item.get("yakin", True)),
        })
    return sorted(hasil, key=lambda x: x["nomor"])


def bersihkan_esai(data: dict) -> list[dict]:
    """Normalisasi hasil ekstraksi teks esai."""
    hasil = [
        {"nomor": int(item["nomor"]), "teks": str(item.get("teks", "")).strip()}
        for item in data.get("jawaban", [])
    ]
    return sorted(hasil, key=lambda x: x["nomor"])


def baca_foto(data_gambar: bytes, jenis: str) -> list[dict]:
    """Baca dan parse foto lembar jawaban. jenis: 'pilihan_ganda' atau 'esai'."""
    gambar = kecilkan_gambar(data_gambar)

    if jenis == "pilihan_ganda":
        return bersihkan_pilihan_ganda(baca_dengan_ai(gambar, PROMPT_PILIHAN_GANDA))

    if jenis == "esai":
        return bersihkan_esai(baca_dengan_ai(gambar, PROMPT_ESAI))

    raise ValueError("Jenis scan harus 'pilihan_ganda' atau 'esai'")


def nilai_pilihan_ganda(terbaca: list[dict], kunci: dict[str, str], total_soal: int | None = None) -> dict:
    """Cocokkan hasil scan dengan kunci jawaban pilihan ganda."""
    peta = {j["nomor"]: j["pilihan"] for j in terbaca}

    daftar_nomor = set(int(k) for k in kunci.keys())
    if total_soal:
        daftar_nomor.update(range(1, total_soal + 1))
    elif terbaca:
        maks_nomor_terbaca = max(j["nomor"] for j in terbaca)
        maks_nomor_kunci = max(daftar_nomor) if daftar_nomor else 0
        daftar_nomor.update(range(1, max(maks_nomor_terbaca, maks_nomor_kunci) + 1))

    nomor_urut = sorted(daftar_nomor)
    detail = []
    benar = 0
    salah = 0
    kosong = 0

    for nomor in nomor_urut:
        huruf_kunci = kunci.get(str(nomor)) or kunci.get(nomor)
        huruf_kunci_clean = huruf_kunci.strip().lower() if huruf_kunci else None
        jawaban = peta.get(nomor)

        if jawaban is None or jawaban == "":
            status = "kosong"
            kosong += 1
        elif huruf_kunci_clean and jawaban == huruf_kunci_clean:
            status = "benar"
            benar += 1
        else:
            status = "salah"
            salah += 1

        detail.append({
            "nomor": nomor,
            "jawaban": (jawaban.upper() if jawaban else None),
            "kunci": (huruf_kunci_clean.upper() if huruf_kunci_clean else None),
            "status": status,
        })

    total = len(nomor_urut)
    nilai = round((benar / total) * 100, 2) if total > 0 else 0.0

    return {
        "total_soal": total,
        "benar": benar,
        "salah": salah,
        "kosong": kosong,
        "nilai": nilai,
        "detail": detail,
    }
