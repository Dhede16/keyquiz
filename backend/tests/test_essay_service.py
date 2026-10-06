import unittest
from unittest.mock import patch

from app.services.essay_service import nilai_esai


class NilaiEsaiTests(unittest.TestCase):
    @patch("app.services.essay_service.panggil_ai_json")
    @patch("app.services.essay_service.es.simpan_jawaban")
    @patch("app.services.essay_service.es.cari_kunci")
    @patch("app.services.essay_service.es.buat_embedding", return_value=[0.1, 0.2])
    def test_scores_each_rubric_criterion_and_keeps_similarity_separate(
        self, _embedding, cari_kunci, _simpan, panggil_ai
    ):
        cari_kunci.return_value = {
            "kunci": "Fotosintesis mengubah energi cahaya menjadi energi kimia.",
            "soal": "Apa fungsi fotosintesis?",
            "rubrik": ["Menjelaskan konversi energi", "Menyebutkan energi kimia"],
            "similarity": 91.25,
        }
        panggil_ai.return_value = {
            "rubric_results": [
                {"score": 0.5, "reason": "Sebagian dijelaskan.", "evidence": "energi"},
                {"score": 1, "reason": "Konsep disebutkan.", "evidence": "energi kimia"},
            ],
            "alasan_ai": "Jawaban benar tetapi belum lengkap.",
        }

        result = nilai_esai("detail-1", "soal-1", "Fotosintesis menghasilkan energi kimia.")

        self.assertEqual(result["similarity"], 91.25)
        self.assertEqual(result["nilai_ai"], 75.0)
        self.assertEqual(result["kategori"], "Cukup")
        self.assertEqual(
            [item["fulfilled"] for item in result["rubric_results"]],
            [False, True],
        )
        self.assertEqual(
            [item["criterion"] for item in result["rubric_results"]],
            ["Menjelaskan konversi energi", "Menyebutkan energi kimia"],
        )

    @patch("app.services.essay_service.panggil_ai_json")
    @patch("app.services.essay_service.es.simpan_jawaban")
    @patch("app.services.essay_service.es.cari_kunci")
    @patch("app.services.essay_service.es.buat_embedding", return_value=[0.1, 0.2])
    def test_uses_answer_key_as_a_single_criterion_when_rubric_is_empty(
        self, _embedding, cari_kunci, _simpan, panggil_ai
    ):
        cari_kunci.return_value = {
            "kunci": "Jawaban acuan.",
            "soal": "Pertanyaan.",
            "rubrik": [],
            "similarity": 80,
        }
        panggil_ai.return_value = {
            "rubric_results": [
                {"score": 0.8, "reason": "Hampir lengkap.", "evidence": "bukti"}
            ],
            "alasan_ai": "Sebagian besar benar.",
        }

        result = nilai_esai("detail-2", "soal-2", "Jawaban mahasiswa.")

        self.assertEqual(result["nilai_ai"], 80)
        self.assertIn("Jawaban acuan.", result["rubric_results"][0]["criterion"])

    @patch("app.services.essay_service.panggil_ai_json")
    @patch("app.services.essay_service.es.simpan_jawaban")
    @patch("app.services.essay_service.es.cari_kunci")
    @patch("app.services.essay_service.es.buat_embedding", return_value=[0.1, 0.2])
    def test_rejects_invalid_rubric_scores_instead_of_silently_grading(
        self, _embedding, cari_kunci, _simpan, panggil_ai
    ):
        cari_kunci.return_value = {
            "kunci": "Acuan.",
            "soal": "Pertanyaan.",
            "rubrik": ["Kriteria."],
            "similarity": 80,
        }
        panggil_ai.return_value = {
            "rubric_results": [
                {"score": 1.5, "reason": "Alasan.", "evidence": ""}
            ],
            "alasan_ai": "",
        }

        with self.assertRaisesRegex(ValueError, "tidak valid"):
            nilai_esai("detail-3", "soal-3", "Jawaban mahasiswa.")

    @patch("app.services.essay_service.panggil_ai_json")
    @patch("app.services.essay_service.es.simpan_jawaban")
    @patch("app.services.essay_service.es.cari_kunci")
    @patch("app.services.essay_service.es.buat_embedding", return_value=[0.1, 0.2])
    def test_discards_evidence_not_found_in_the_student_answer(
        self, _embedding, cari_kunci, _simpan, panggil_ai
    ):
        cari_kunci.return_value = {
            "kunci": "Acuan.",
            "soal": "Pertanyaan.",
            "rubrik": ["Kriteria."],
            "similarity": 80,
        }
        panggil_ai.return_value = {
            "rubric_results": [
                {"score": 1, "reason": "Alasan.", "evidence": "kutipan yang dikarang"}
            ],
            "alasan_ai": "",
        }

        result = nilai_esai("detail-5", "soal-5", "Teks jawaban mahasiswa.")

        self.assertEqual(result["rubric_results"][0]["evidence"], "")

    @patch("app.services.essay_service.es.buat_embedding")
    def test_empty_answer_returns_zero_without_embedding_or_llm(self, embedding):
        result = nilai_esai("detail-4", "soal-4", "  ")

        self.assertEqual(result["nilai_ai"], 0)
        self.assertEqual(result["rubric_results"], [])
        embedding.assert_not_called()


if __name__ == "__main__":
    unittest.main()
