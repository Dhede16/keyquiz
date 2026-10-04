"""Penilaian esai berdasarkan kemiripan embedding dengan kunci jawaban."""
from app.services import embedding_service as es


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


def nilai_esai(id_detail: str, id_soal: str, jawaban_teks: str) -> dict:
    """Gunakan persentase kemiripan embedding sebagai nilai AI esai."""
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

    vektor = es.buat_embedding(jawaban_teks)
    data_kunci = es.cari_kunci(vektor, id_soal)
    es.simpan_jawaban(id_detail, id_soal, jawaban_teks, vektor)
    similarity = round(data_kunci["similarity"], 2)

    return {
        "id_detail": id_detail,
        "id_soal": id_soal,
        "similarity": similarity,
        "nilai_ai": similarity,
        "kategori": tentukan_kategori(similarity),
        "status": "Nilai ditentukan berdasarkan kemiripan embedding dengan kunci jawaban",
    }
