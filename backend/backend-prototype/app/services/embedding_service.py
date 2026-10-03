"""Service Embedding teks dan manajemen koleksi ChromaDB."""
import json
import chromadb
from sentence_transformers import SentenceTransformer
from app.config import CHROMA_DB_PATH, NAMA_MODEL_EMBEDDING

model = SentenceTransformer(NAMA_MODEL_EMBEDDING)
klien = chromadb.PersistentClient(path=CHROMA_DB_PATH)

koleksi_kunci = klien.get_or_create_collection(
    name="kunci_jawaban", metadata={"hnsw:space": "cosine"}
)
koleksi_jawaban = klien.get_or_create_collection(
    name="jawaban_mahasiswa", metadata={"hnsw:space": "cosine"}
)


def buat_embedding(teks: str) -> list[float]:
    """Mengubah teks menjadi vektor embedding ternormalisasi."""
    return model.encode(teks, normalize_embeddings=True).tolist()


def simpan_kunci(id_kunci: str, id_soal: str, soal: str, kunci_teks: str, rubrik: list[str]) -> None:
    """Simpan kunci jawaban beserta soal dan rubriknya ke ChromaDB."""
    koleksi_kunci.upsert(
        ids=[id_kunci],
        embeddings=[buat_embedding(kunci_teks)],
        documents=[kunci_teks],
        metadatas=[{
            "id_soal": id_soal,
            "soal": soal,
            "rubrik": json.dumps(rubrik),
        }],
    )


def cari_kunci(vektor_jawaban: list[float], id_soal: str) -> dict:
    """Ambil kunci milik soal dan hitung cosine similarity (skala 0-100)."""
    hasil = koleksi_kunci.query(
        query_embeddings=[vektor_jawaban],
        n_results=1,
        where={"id_soal": id_soal},
    )
    if not hasil["ids"][0]:
        raise ValueError(f"Kunci jawaban untuk id_soal '{id_soal}' belum disimpan")

    meta = hasil["metadatas"][0][0]
    similarity = (1 - hasil["distances"][0][0]) * 100

    return {
        "kunci": hasil["documents"][0][0],
        "soal": meta["soal"],
        "rubrik": json.loads(meta["rubrik"]),
        "similarity": max(0.0, min(100.0, similarity)),
    }


def simpan_jawaban(id_detail: str, id_soal: str, jawaban_teks: str, vektor: list[float]) -> None:
    """Simpan embedding jawaban mahasiswa (id_detail = id DETAIL_JAWABAN)."""
    koleksi_jawaban.upsert(
        ids=[id_detail],
        embeddings=[vektor],
        documents=[jawaban_teks],
        metadatas=[{"id_soal": id_soal}],
    )
