import unittest

from app.services.scan_service import bersihkan_pilihan_ganda


class ScanServiceTests(unittest.TestCase):
    def test_normalizes_question_options_and_marked_answer(self):
        result = bersihkan_pilihan_ganda(
            {
                "jawaban": [
                    {
                        "nomor": 2,
                        "pertanyaan": "  Berapa hasil 2 + 2? ",
                        "opsi": [
                            {"huruf": "A", "teks": "3"},
                            {"huruf": "B", "teks": "4"},
                        ],
                        "pilihan_dipilih": "B",
                        "yakin": False,
                    }
                ]
            }
        )

        self.assertEqual(
            result,
            [
                {
                    "nomor": 2,
                    "pertanyaan": "Berapa hasil 2 + 2?",
                    "opsi": [
                        {"huruf": "a", "teks": "3"},
                        {"huruf": "b", "teks": "4"},
                    ],
                    "pilihan": "b",
                    "kunci_jawaban": None,
                    "kunci_yakin": False,
                    "bobot": 100.0,
                    "nilai_ai": 0,
                    "status_ai": "kosong",
                    "yakin": False,
                }
            ],
        )

    def test_discards_marked_answer_that_is_not_an_extracted_option(self):
        result = bersihkan_pilihan_ganda(
            {
                "jawaban": [
                    {
                        "nomor": 1,
                        "opsi": [{"huruf": "A", "teks": "Pilihan A"}],
                        "pilihan_dipilih": "D",
                    }
                ]
            }
        )

        self.assertIsNone(result[0]["pilihan"])

    def test_uses_ai_answer_key_and_normalizes_weights_to_exactly_100(self):
        result = bersihkan_pilihan_ganda(
            {
                "jawaban": [
                    {
                        "nomor": 2,
                        "pertanyaan": "Question 2",
                        "opsi": [{"huruf": "a", "teks": "A"}, {"huruf": "b", "teks": "B"}],
                        "pilihan_dipilih": "b",
                        "kunci_jawaban": "b",
                        "bobot": 1,
                    },
                    {
                        "nomor": 1,
                        "pertanyaan": "Question 1",
                        "opsi": [{"huruf": "a", "teks": "A"}, {"huruf": "b", "teks": "B"}],
                        "pilihan_dipilih": "a",
                        "kunci_jawaban": "b",
                        "bobot": 1,
                    },
                ]
            }
        )

        self.assertEqual([item["nomor"] for item in result], [1, 2])
        self.assertEqual(sum(item["bobot"] for item in result), 100)
        self.assertEqual([item["bobot"] for item in result], [50, 50])
        self.assertEqual(result[0]["nilai_ai"], 0)
        self.assertEqual(result[0]["status_ai"], "salah")
        self.assertEqual(result[1]["nilai_ai"], 50)
        self.assertEqual(result[1]["status_ai"], "benar")

    def test_weight_rounding_preserves_exact_total_for_thirteen_questions(self):
        raw = {
            "jawaban": [
                {
                    "nomor": number,
                    "pertanyaan": f"Question {number}",
                    "opsi": [{"huruf": "a", "teks": "A"}, {"huruf": "b", "teks": "B"}],
                    "kunci_jawaban": "a",
                    "bobot": 1,
                }
                for number in range(1, 14)
            ]
        }
        result = bersihkan_pilihan_ganda(raw)

        self.assertEqual(sum(item["bobot"] for item in result), 100)
        self.assertTrue(all(item["bobot"] > 0 for item in result))


if __name__ == "__main__":
    unittest.main()
