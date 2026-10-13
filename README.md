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
cp frontend/.env.example frontend/.env.local
```
Buka kedua file dan isi placeholder konfigurasi dengan kredensial proyek Anda. Frontend hanya memakai URL Supabase, anon key, dan URL API; **jangan pernah memasukkan service-role key ke variabel `VITE_*`**.
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
NAMA_MODEL_VISION=qwen/qwen3.8-27b
NAMA_MODEL_LLM=qwen/qwen3.8-27b
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

### 4. Inisialisasi Database Supabase
Cadangkan database terlebih dahulu, terutama jika proyek Supabase sudah berisi data. Gunakan direct connection atau session pooler Supabase dengan SSL (hindari transaction pooler untuk migrasi), isi `DATABASE_URL` di `.env`, lalu jalankan:
```bash
python database/init_db.py
```
Script menerapkan `database/schema.sql` lalu semua file `.sql` di `database/migrations/` dalam urutan nama, serta mencatat versi yang selesai di `public.keyquiz_schema_migrations` agar migrasi yang sudah tercatat tidak dijalankan ulang. Jika Anda menjalankan SQL secara manual di Supabase SQL Editor, script mungkin menjalankan ulang migrasi yang belum tercatat; migrasi dirancang aman untuk diulang. Error menghentikan proses dengan status gagal. Perubahan profil memindahkan tanggal lahir, telepon, dan gender ke tabel `profile_private`, menyalin data yang ada, lalu menghapus kolom lama. Jika nilai gender lama tidak valid, migrasi berhenti tanpa menghapus data; periksa dengan:
```sql
SELECT id, gender
FROM public.profiles
WHERE gender IS NOT NULL
  AND gender NOT IN ('laki-laki', 'perempuan');
```
Normalisasi nilai yang ditampilkan sebelum mencoba ulang. Jika tidak memakai koneksi PostgreSQL dari script, jalankan `schema.sql` dan seluruh file migrasi secara berurutan di SQL Editor Supabase.

Untuk database yang sudah berjalan, pastikan backup berhasil dan jalankan saat aplikasi tidak sedang mengubah profil. Jangan menghapus atau mereset tabel/Auth/Storage. Script ini tidak dijalankan otomatis saat build atau deploy.

Migrasi `20261014_access_control_hardening.sql` membatasi pembacaan kelas dan anggota, mewajibkan join kelas melalui kode yang divalidasi database, membatasi akses kunci jawaban, serta memindahkan pengiriman jawaban dan penyimpanan nilai ke fungsi database yang memvalidasi hak akses. Penilaian dosen disimpan dalam satu transaksi; pastikan migrasi ini berhasil diterapkan sebelum deploy frontend/backend yang menggunakannya. Backend penilaian esai juga memerlukan `SUPABASE_SERVICE_ROLE_KEY` yang hanya disimpan di environment backend.

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

## ☁️ Deployment (Vercel + Render)

1. Buat Web Service dari `render.yaml` di Render. Blueprint memakai paket Standard karena model embedding berbasis PyTorch memerlukan memori yang memadai, serta disk persisten untuk menyimpan embedding dan cache model melewati deploy/restart.
2. Isi environment variables backend di Render: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `GROQ_API_KEY`, dan `CORS_ORIGINS`. Atur `CORS_ORIGINS` ke origin frontend yang tepat, misalnya `https://<nama-proyek>.vercel.app` (tanpa trailing slash). Jangan gunakan `*`.
3. Buat proyek di Vercel dengan **Root Directory** `frontend`. File `frontend/vercel.json` mengatur output `dist` dan fallback routing Vue.
4. Isi environment variables Vercel:
   - `VITE_SUPABASE_URL` — URL proyek Supabase.
   - `VITE_SUPABASE_ANON_KEY` — anon/publishable key Supabase.
   - `VITE_API_BASE_URL` — URL backend Render yang diakhiri `/api`, misalnya `https://<nama-service>.onrender.com/api`.
5. Pastikan origin production Vercel tercantum di `CORS_ORIGINS` Render. Jika memakai domain kustom atau preview deployment, masukkan origin yang memang diizinkan.
6. Terapkan migrasi database terlebih dahulu, deploy backend dan frontend, lalu cek backend `/` dan coba login, akses kelas, buat tugas, serta penilaian esai.

`DATABASE_URL` hanya diperlukan untuk menjalankan migrasi dari mesin operator; jangan masukkan ke Vercel atau Render. `SUPABASE_SERVICE_ROLE_KEY` hanya berada di backend Render dan tidak boleh dibagikan ke frontend.

---

## 🎯 Panduan Skenario Pengujian Fitur Utama

Setelah backend dan frontend berjalan, Anda dapat menguji fitur-fitur unggulan berikut:

1. **Pembuatan Soal Otomatis (AI Quiz Generator)**:
   - Buka menu kelas -> Klik tombol **Buat Soal AI**.
   - Ketik instruksi materi (misal: *"Buatkan kuis tentang fotosintesis"*).
   - AI akan secara langsung membuat butir soal PG, esai, beserta kunci jawaban dan rubrik penilaian.

2. **Pemindaian Lembar Jawaban Kertas (Vision AI Scan)**:
   - Buka menu **Scan Soal** pada navigasi sidebar.
   - Unggah satu foto JPG, PNG, atau WEBP berisi soal pilihan ganda beserta tanda jawaban siswa.
   - Periksa hasil ekstraksi teks soal dan keterangan setiap opsi. AI menyarankan kunci jawaban dan bobot tiap soal, lalu dosen dapat mengubah keduanya serta menyesuaikan nilai jawaban.
   - Pastikan total bobot semua soal tepat 100 poin sebelum memilih kelas dan mahasiswa untuk mengirim hasil.
   - Pilih kelas dan satu mahasiswa, lalu kirim hasil. Hasil scan, jawaban, dan nilai tersimpan sebagai tugas di kelas tersebut dan dapat dilihat mahasiswa pada detail tugas.
   - Pastikan migrasi `20261004_scanned_results_student_privacy.sql` sudah diterapkan; RLS membatasi tugas scan, pertanyaan, dan opsi kepada dosen kelas serta mahasiswa tujuan.
   - Pastikan migrasi `20261006_scanned_sheet_archives.sql` sudah diterapkan agar foto asli dan koreksi tersimpan di arsip kelas. `database/init_db.py` menjalankan kedua migrasi tersebut secara otomatis.

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
├── render.yaml               # Blueprint backend Render + disk persisten
├── README.md                 # Dokumentasi panduan lengkap proyek
├── AGENTS.md                 # Panduan arsitektur & aturan pengembangan
│
├── database/                 # Skema & Inisialisasi Database
│   ├── schema.sql            # Baseline Supabase (tabel, trigger, RLS)
│   ├── init_db.py            # Runner schema + migrasi berurutan
│   └── migrations/           # Perubahan SQL forward-only
│
├── backend/                  # Layanan Backend FastAPI
│   ├── .python-version       # Versi Python deployment
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
    ├── vercel.json           # Build dan fallback routing SPA
    ├── .env.example          # Template konfigurasi frontend
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
