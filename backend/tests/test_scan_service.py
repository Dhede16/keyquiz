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


if __name__ == "__main__":
    unittest.main()
