"""Service Embedding teks dan koleksi ChromaDB."""
import json
import chromadb
from sentence_transformers import SentenceTransformer
from app.config import CHROMA_DB_PATH, NAMA_MODEL_EMBEDDING

_model = None
_chroma_client = None
_koleksi_kunci = None
_koleksi_jawaban = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(NAMA_MODEL_EMBEDDING)
    return _model


def get_chroma():
    global _chroma_client, _koleksi_kunci, _koleksi_jawaban
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        _koleksi_kunci = _chroma_client.get_or_create_collection(
            name="kunci_jawaban", metadata={"hnsw:space": "cosine"}
        )
        _koleksi_jawaban = _chroma_client.get_or_create_collection(
            name="jawaban_mahasiswa", metadata={"hnsw:space": "cosine"}
        )
    return _koleksi_kunci, _koleksi_jawaban


def buat_embedding(teks: str) -> list[float]:
    """Mengubah teks menjadi vektor embedding ternormalisasi."""
    model = get_model()
    return model.encode(teks, normalize_embeddings=True).tolist()


def simpan_kunci(id_kunci: str, id_soal: str, soal: str, kunci_teks: str, rubrik: list[str]) -> None:
    """Simpan kunci jawaban beserta soal dan rubriknya ke ChromaDB."""
    koleksi_kunci, _ = get_chroma()
    existing_ids = koleksi_kunci.get(where={"id_soal": id_soal})["ids"]
    koleksi_kunci.upsert(
        ids=[id_kunci],
        embeddings=[buat_embedding(kunci_teks)],
        documents=[kunci_teks],
        metadatas=[{
            "id_soal": id_soal,
            "soal": soal,
            "rubrik": json.dumps(rubrik if isinstance(rubrik, list) else []),
        }],
    )
    stale_ids = [existing_id for existing_id in existing_ids if existing_id != id_kunci]
    if stale_ids:
        koleksi_kunci.delete(ids=stale_ids)


def cari_kunci(vektor_jawaban: list[float], id_soal: str) -> dict:
    """Ambil kunci milik soal dan hitung cosine similarity (skala 0-100)."""
    koleksi_kunci, _ = get_chroma()
    hasil = koleksi_kunci.query(
        query_embeddings=[vektor_jawaban],
        n_results=1,
        where={"id_soal": id_soal},
    )
    if not hasil["ids"] or not hasil["ids"][0]:
        raise ValueError(f"Kunci jawaban untuk id_soal '{id_soal}' belum disimpan di basis data vektor")

    meta = hasil["metadatas"][0][0]
    similarity = (1 - hasil["distances"][0][0]) * 100

    return {
        "kunci": hasil["documents"][0][0],
        "soal": meta["soal"],
        "rubrik": json.loads(meta["rubrik"]) if meta.get("rubrik") else [],
        "similarity": max(0.0, min(100.0, similarity)),
    }


def simpan_jawaban(id_detail: str, id_soal: str, jawaban_teks: str, vektor: list[float]) -> None:
    """Simpan embedding jawaban mahasiswa."""
    _, koleksi_jawaban = get_chroma()
    koleksi_jawaban.upsert(
        ids=[id_detail],
        embeddings=[vektor],
        documents=[jawaban_teks],
        metadatas=[{"id_soal": id_soal}],
    )
