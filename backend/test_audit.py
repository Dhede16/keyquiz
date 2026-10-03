"""Comprehensive Automated Audit & Regression Test Suite for KeyQuiz Backend."""
import sys
import os
from unittest.mock import MagicMock, patch

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.services import scan_service as ss
from app.services import essay_service as es

client = TestClient(app)

def test_health_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert "version" in data
    print("[PASS] Health check endpoint PASSED")

def test_tentukan_kategori():
    assert es.tentukan_kategori(95.0) == "Sangat Baik"
    assert es.tentukan_kategori(90.0) == "Sangat Baik"
    assert es.tentukan_kategori(85.0) == "Baik"
    assert es.tentukan_kategori(80.0) == "Baik"
    assert es.tentukan_kategori(75.0) == "Cukup"
    assert es.tentukan_kategori(70.0) == "Cukup"
    assert es.tentukan_kategori(65.0) == "Kurang"
    assert es.tentukan_kategori(60.0) == "Kurang"
    assert es.tentukan_kategori(59.9) == "Sangat Kurang"
    assert es.tentukan_kategori(0.0) == "Sangat Kurang"
    print("[PASS] Essay predicate categorization logic PASSED")

def test_nilai_esai_empty_input():
    res = es.nilai_esai("detail-1", "soal-1", "")
    assert res["nilai_ai"] == 0.0
    assert res["kategori"] == "Sangat Kurang"
    assert res["status"] == "Jawaban kosong"
    print("[PASS] Empty essay submission edge case PASSED")

def test_scan_service_cleaning_and_scoring():
    raw_pg = {
        "jawaban": [
            {"nomor": 2, "pilihan": " B ", "yakin": True},
            {"nomor": 1, "pilihan": "a", "yakin": True},
            {"nomor": 3, "pilihan": "Z", "yakin": False},
            {"nomor": 4, "pilihan": None, "yakin": True},
        ]
    }
    cleaned = ss.bersihkan_pilihan_ganda(raw_pg)
    assert len(cleaned) == 4
    assert [x["nomor"] for x in cleaned] == [1, 2, 3, 4]
    assert cleaned[0]["pilihan"] == "a"
    assert cleaned[1]["pilihan"] == "b"
    assert cleaned[2]["pilihan"] is None
    assert cleaned[3]["pilihan"] is None

    kunci = {"1": "A", "2": "C", "3": "B", "4": "D"}
    rekap = ss.nilai_pilihan_ganda(cleaned, kunci, total_soal=4)
    assert rekap["total_soal"] == 4
    assert rekap["benar"] == 1
    assert rekap["salah"] == 1
    assert rekap["kosong"] == 2
    assert rekap["nilai"] == 25.0
    print("[PASS] Vision Scan MC cleaning & grading logic PASSED")

def test_api_validation_errors():
    resp = client.post(
        "/api/scan",
        files={"file": ("test.txt", b"plain text", "text/plain")},
        data={"jenis": "pilihan_ganda"}
    )
    assert resp.status_code == 400
    assert "tidak didukung" in resp.json()["detail"]

    resp = client.post(
        "/api/ai/generate-quiz",
        json={"prompt": "   ", "jumlah_pg": 3, "jumlah_esai": 2}
    )
    assert resp.status_code == 400
    print("[PASS] API Schema & Boundary Validation tests PASSED")

if __name__ == "__main__":
    print("=" * 60)
    print("Running KeyQuiz Backend Audit Tests...")
    print("=" * 60)
    test_health_endpoint()
    test_tentukan_kategori()
    test_nilai_esai_empty_input()
    test_scan_service_cleaning_and_scoring()
    test_api_validation_errors()
    print("=" * 60)
    print("ALL AUDIT UNIT & INTEGRATION TESTS PASSED (5/5)!")
    print("=" * 60)
