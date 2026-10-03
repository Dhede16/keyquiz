# KeyQuiz - Sistem Penilaian Esai AI & Pemindaian Jawaban Kertas

Aplikasi web cerdas untuk evaluasi pembelajaran yang menggabungkan **Penilaian Esai Otomatis (Semantic Similarity + LLM Rubrik)**, **Pembuatan Soal Otomatis (AI Quiz Generator)**, dan **Pemindaian Lembar Jawaban Kertas (Vision AI OCR)**.

Dikembangkan oleh **Tim Borneo IT** untuk ajang **ICONFEST 2026 (Software Development Competition)**.

---

## 🛠️ Tech Stack

- **Frontend**: Vue.js 3 (*Composition API*), Vite 7, Tailwind CSS v4, Vue Router 4.
- **Backend**: FastAPI (Python 3.10+), Uvicorn, Pydantic v2.
- **Database & Storage**: Supabase (PostgreSQL + Auth + Storage) & ChromaDB (Vector Embeddings).
- **AI & NLP Engine**:
  - **Sentence Transformers** (`all-MiniLM-L6-v2`) untuk *Semantic Embedding*.
  - **Groq AI / Qwen / Llama 3.3 70B** untuk evaluasi kriteria rubrik & generator kuis.
  - **Llama 3.2 Vision / Qwen Vision** untuk ekstraksi lembar ujian fisik (*OCR*).

---

## 📋 Prasyarat Sistem (Prerequisites)

Sebelum menjalankan proyek, pastikan perangkat Anda telah terpasang:
1. **Node.js** (Versi 18+ atau 20+ disarankan) & `npm`
2. **Python** (Versi 3.10, 3.11, 3.12, atau 3.13) & `pip`
3. Akun dan API Key **Groq Cloud** ([console.groq.com](https://console.groq.com/keys))
4. Project **Supabase** ([supabase.com](https://supabase.com))

---

## 🚀 Panduan Menjalankan Proyek dari Nol (0 to 100)

### 1. Kloning Repositori & Masuk ke Folder
```bash
git clone https://github.com/Dhede16/keyquiz.git
cd keyquiz
```

---

### 2. Konfigurasi Environment (`.env`)
Salin file `.env.example` di root project menjadi `.env`:
```bash
cp .env.example .env
```
Buka file `.env` dan pastikan konfigurasi telah terisi:
```env
# Server
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres:your-password@db.your-project.supabase.co:5432/postgres

# Groq AI
GROQ_API_KEY=gsk_your_groq_api_key_here
NAMA_MODEL_VISION=llama-3.2-11b-vision-preview
NAMA_MODEL_LLM=llama-3.3-70b-versatile
NAMA_MODEL_EMBEDDING=all-MiniLM-L6-v2

# ChromaDB
CHROMA_DB_PATH=./chroma_db
```

---

### 3. Setup & Instalasi Dependensi Backend
Buka terminal dan jalankan instalasi paket Python yang dibutuhkan:
```bash
pip install -r backend/requirements.txt
```

---

### 4. Inisialisasi Database Supabase (Otomatis)
Jalankan script Python berikut untuk membuat seluruh tabel (`profiles`, `kelas`, `tugas`, `soal`, `detail_jawaban`, dll.), trigger registrasi profil otomatis, dan aturan Row Level Security (RLS) di Supabase:
```bash
python database/init_db.py
```
> **Output Sukses:** `[SUKSES] Semua tabel, trigger, dan RLS policy berhasil dibuat di Supabase!`

---

### 5. Setup & Instalasi Dependensi Frontend
Buka terminal baru, masuk ke folder `frontend` dan install dependensi Node:
```bash
cd frontend
npm install
```

---

### 6. Menjalankan Aplikasi (Development Mode)

Jalankan kedua server secara bersamaan di terminal terpisah:

#### **Terminal 1 — Menjalankan Backend FastAPI:**
```bash
cd backend
python main.py
```
- Server backend aktif di: `http://127.0.0.1:8000`
- Dokumentasi interaktif Swagger API: `http://127.0.0.1:8000/docs`

#### **Terminal 2 — Menjalankan Frontend Vue.js:**
```bash
cd frontend
npm run dev
```
- Aplikasi web aktif di: `http://localhost:5173`

---

## 🎯 Panduan Skenario Pengujian Fitur Utama

Setelah backend dan frontend berjalan, Anda dapat menguji fitur-fitur unggulan berikut:

1. **Pembuatan Soal Otomatis (AI Quiz Generator)**:
   - Buka menu kelas -> Klik tombol **Buat Soal AI**.
   - Ketik instruksi materi (misal: *"Buatkan kuis tentang fotosintesis"*).
   - AI akan secara langsung membuat butir soal PG, esai, beserta kunci jawaban dan rubrik penilaian.

2. **Pemindaian Lembar Jawaban Kertas (Vision AI Scan)**:
   - Buka menu **Scan Soal** pada navigasi sidebar.
   - Unggah foto lembar jawaban kertas (contoh foto sampel tersedia di [backend/backend-prototype/foto-testing-scan](file:///c:/Users/NITRO/supercode/keyquiz/backend/backend-prototype/foto-testing-scan)).
   - AI Vision akan mengekstrak opsi jawaban siswa dan mencocokkannya secara instan dengan kunci jawaban.

3. **Penilaian Esai Semantik (Hybrid Grading Engine)**:
   - Mahasiswa mengumpulkan jawaban esai pada halaman detail tugas.
   - Sistem membandingkan jawaban dengan kunci secara semantik melalui ChromaDB Vektor Embedding.
   - Jika jawaban berada pada rentang skor menengah (30% - 90%), LLM akan memeriksa kesesuaian rubrik kriteria dan kelengkapan secara otomatis.
   - Dosen dapat meninjau `nilai_ai` dan menentukan `nilai_final`.

---

## 📁 Struktur Direktori Proyek

```text
keyquiz/
├── .env.example              # Template konfigurasi environment
├── .env                      # File konfigurasi aktif (credentials)
├── README.md                 # Dokumentasi panduan lengkap proyek
├── AGENTS.md                 # Panduan arsitektur & aturan pengembangan
│
├── database/                 # Skema & Inisialisasi Database
│   ├── schema.sql            # DDL SQL Supabase (Tables, Triggers, RLS)
│   └── init_db.py            # Script inisialisasi tabel otomatis
│
├── backend/                  # Layanan Backend FastAPI
│   ├── main.py               # Launcher utama backend server
│   ├── requirements.txt      # Daftar dependensi Python
│   ├── docs/                 # Laporan & proposal proyek ICONFEST 2026
│   └── app/
│       ├── config.py         # Global configuration loader
│       ├── main.py           # FastAPI app & CORS middleware
│       ├── core/             # Client Supabase & Groq AI
│       ├── services/         # Embedding, Essay grading, Scan, Quiz generator
│       └── api/              # Route endpoints (/api/essay, /api/scan, /api/ai)
│
└── frontend/                 # Antarmuka Pengguna Vue.js 3
    ├── package.json          # Dependensi frontend & scripts
    ├── vite.config.js        # Konfigurasi Vite & Tailwind CSS
    └── src/
        ├── services/api.js   # HTTP Client ke backend FastAPI
        ├── composables/      # State management (useAuth, useClasses)
        ├── router/           # Routing & navigation guards
        ├── views/            # Halaman Dashboard, ScanSoal, BuatSoal, TaskDetail
        └── components/       # Komponen UI modular
```

---

## 👥 Tim Pengembang (Borneo IT)
- **Dhede Febrian Purnawiranto** — Ketua Tim (256151011)
- **Affan** — Anggota (256151002)
- **Winner** — Anggota (256151025)

**Politeknik Negeri Samarinda — ICONFEST 2026**
