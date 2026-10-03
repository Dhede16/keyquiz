/**
 * KeyQuiz API Client Service
 * Menghubungkan antarmuka frontend Vue ke backend FastAPI.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

/**
 * Panggil AI untuk membuat soal pilihan ganda & esai secara otomatis.
 */
export async function generateQuizAI({ prompt, jumlahPg = 3, jumlahEsai = 2 }) {
  const response = await fetch(`${API_BASE_URL}/ai/generate-quiz`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt,
      jumlah_pg: Number(jumlahPg),
      jumlah_esai: Number(jumlahEsai),
    }),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || 'Gagal menghasilkan soal dari AI.')
  }

  const result = await response.json()
  return result.data
}

/**
 * Scan lembar jawaban fisik dengan Vision AI.
 */
export async function scanAnswerSheet({ file, jenis = 'pilihan_ganda', kunci = null, totalSoal = null }) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('jenis', jenis)
  if (kunci) {
    formData.append('kunci', typeof kunci === 'string' ? kunci : JSON.stringify(kunci))
  }
  if (totalSoal) {
    formData.append('total_soal', totalSoal)
  }

  const response = await fetch(`${API_BASE_URL}/scan`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || 'Gagal memindai lembar jawaban dengan Vision AI.')
  }

  return await response.json()
}

/**
 * Simpan kunci jawaban dan rubrik esai ke vector database (ChromaDB).
 */
export async function saveEssayKey({ idKunci, idSoal, soal, kunciTeks, rubrik = [] }) {
  const response = await fetch(`${API_BASE_URL}/essay/kunci`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      id_kunci: String(idKunci),
      id_soal: String(idSoal),
      soal,
      kunci_teks: kunciTeks,
      rubrik,
    }),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || 'Gagal menyimpan kunci jawaban esai.')
  }

  return await response.json()
}

/**
 * Nilai jawaban esai mahasiswa secara otomatis (Semantic Similarity + LLM Rubrik).
 */
export async function gradeEssay({ idDetail, idSoal, jawabanTeks }) {
  const response = await fetch(`${API_BASE_URL}/essay/nilai`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      id_detail: String(idDetail),
      id_soal: String(idSoal),
      jawaban_teks: jawabanTeks,
    }),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || 'Gagal melakukan penilaian esai AI.')
  }

  return await response.json()
}
