# KeyQuiz

**Platform evaluasi pembelajaran berbantuan AI** untuk membantu pengajar membuat kuis, menilai jawaban, dan memproses lembar jawaban.

Dikembangkan oleh **Tim Borneo IT** untuk **ICONFEST 2026 — Software Development Competition**.

## Tentang proyek

KeyQuiz menghubungkan pengajar dan mahasiswa dalam satu alur evaluasi. Pengajar dapat mengelola kelas dan tugas, membuat kuis secara manual maupun dengan bantuan AI, serta meninjau hasil penilaian. Mahasiswa dapat bergabung ke kelas, mengerjakan tugas, dan melihat hasil sesuai pengaturan tugas.

## Fitur utama

- **Manajemen kelas dan tugas** — alur untuk pengajar dan mahasiswa, termasuk bergabung ke kelas menggunakan kode.
- **Pembuatan kuis berbantuan AI** — membuat draf soal pilihan ganda dan esai dari instruksi pengajar.
- **Penilaian esai berbantuan AI** — membandingkan jawaban dengan acuan dan menilai kriteria rubrik; pengajar tetap dapat meninjau hasilnya.
- **Pemindaian lembar jawaban** — mengekstrak jawaban dari foto JPG, PNG, atau WEBP dan membantu memeriksa hasil sebelum disimpan.
- **Penyimpanan dan kontrol akses** — Supabase menyediakan autentikasi, database, penyimpanan, dan kebijakan akses.

> Hasil AI adalah bantuan penilaian, bukan pengganti keputusan pengajar. Tinjau soal, hasil ekstraksi, dan nilai sebelum digunakan.

## Teknologi

| Bagian | Teknologi |
| --- | --- |
| Frontend | Vue 3, Vue Router, Vite, Tailwind CSS |
| Backend API | Python 3.12, FastAPI, Uvicorn |
| Database dan autentikasi | Supabase (PostgreSQL, Auth, Storage) |
| AI | Groq API dengan model Qwen (`qwen/qwen3.8-27b`) untuk pembuatan kuis, penilaian rubrik, dan pemrosesan gambar |
| Embedding | Hugging Face Inference API bila token tersedia; fallback embedding lokal |

## Menjalankan secara lokal

### Prasyarat

- Git
- Node.js **20.19+** atau **22.12+**, beserta npm
- Python **3.12**
- Proyek Supabase dan API key Groq untuk fitur AI

### 1. Ambil kode dan siapkan konfigurasi

```powershell
git clone https://github.com/Dhede16/keyquiz.git
cd keyquiz
Copy-Item .env.example .env
Copy-Item frontend/.env.example frontend/.env.local
```

Perintah penyalinan di atas ditujukan untuk PowerShell. Isi nilai konfigurasi pada kedua file sesuai lingkungan lokal Anda.

#### Backend — `.env`

| Variabel | Kegunaan |
| --- | --- |
| `SUPABASE_URL` | URL proyek Supabase |
| `SUPABASE_ANON_KEY` | Anon/publishable key Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | Operasi admin backend; rahasiakan dan jangan pernah taruh di frontend |
| `GROQ_API_KEY` | Akses model AI |
| `DATABASE_URL` | Koneksi PostgreSQL untuk menjalankan inisialisasi skema dan migrasi |
| `CORS_ORIGINS` | Daftar origin frontend yang diizinkan, dipisahkan koma |
| `PORT` | Port API; default `8000` |

Model Groq default untuk pembuatan kuis dan pemrosesan gambar adalah `qwen/qwen3.8-27b`, sesuai konfigurasi proyek. Model dapat diatur melalui `NAMA_MODEL_LLM` dan `NAMA_MODEL_VISION`; embedding dapat diatur melalui `NAMA_MODEL_EMBEDDING`. `HF_TOKEN` atau `HUGGINGFACE_API_KEY` bersifat opsional untuk embedding melalui Hugging Face.

#### Frontend — `frontend/.env.local`

| Variabel | Kegunaan |
| --- | --- |
| `VITE_SUPABASE_URL` | URL proyek Supabase |
| `VITE_SUPABASE_ANON_KEY` | Anon/publishable key Supabase |
| `VITE_API_BASE_URL` | URL dasar API, lokal: `http://127.0.0.1:8000/api` |

Variabel dengan awalan `VITE_` tersedia di browser. Jangan masukkan `SUPABASE_SERVICE_ROLE_KEY`, `GROQ_API_KEY`, atau kredensial server lainnya ke variabel tersebut.

### 2. Pasang dependensi

Buat dan aktifkan virtual environment Python, lalu pasang dependensi backend:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
```

Pasang dependensi frontend:

```powershell
Set-Location frontend
npm install
Set-Location ..
```

### 3. Siapkan database

Pastikan `DATABASE_URL` mengarah ke proyek Supabase yang benar, lalu dari folder root jalankan:

```powershell
python database/init_db.py
```

Perintah tersebut menerapkan `database/schema.sql` dan migrasi SQL secara berurutan. Gunakan database pengembangan atau pastikan Anda memiliki backup sebelum menjalankan migrasi pada database berisi data.

### 4. Jalankan aplikasi

Buka dua terminal dari folder root proyek.

Terminal pertama — API:

```powershell
python backend/main.py
```

Terminal kedua — frontend:

```powershell
Set-Location frontend
npm run dev
```

Buka frontend pada `http://localhost:5173`. API tersedia di `http://127.0.0.1:8000`; dokumentasi interaktif tersedia di `http://127.0.0.1:8000/docs`.

## API utama

| Method | Endpoint | Kegunaan |
| --- | --- | --- |
| `POST` | `/api/auth/register-admin` | Pendaftaran akun |
| `POST` | `/api/ai/generate-quiz` | Membuat draf kuis dengan AI |
| `POST` | `/api/scan` | Membaca lembar jawaban dari gambar |
| `POST` | `/api/essay/kunci` | Menyimpan kunci dan rubrik esai |
| `POST` | `/api/essay/nilai` | Menilai jawaban esai |

## Pengujian dan build

Jalankan tes backend dari folder root:

```powershell
Set-Location backend
python -m unittest discover -s tests
Set-Location ..
```

Buat build frontend produksi:

```powershell
Set-Location frontend
npm run build
```

## Struktur repositori

```text
backend/       FastAPI API dan layanan AI
database/      Skema Supabase dan migrasi
frontend/      Aplikasi web Vue
```

## Tim

**Borneo IT** — Politeknik Negeri Samarinda

- Dhede Febrian Purnawiranto — Ketua Tim
- Affan — Anggota
- Winner — Anggota

## Lisensi

Kode proyek ini menggunakan **MIT License**; lihat [LICENSE](./LICENSE). Lisensi ini tidak menggantikan ketentuan ICONFEST atau lisensi aset pihak ketiga yang mungkin digunakan proyek.
