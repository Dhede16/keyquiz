# Langkah Memperbaiki Supabase sampai KeyQuiz Ter-deploy

Panduan ini untuk menyiapkan Supabase yang sudah dipakai KeyQuiz, menerapkan skema/migrasi tanpa mereset data, lalu deploy backend ke Render dan frontend ke Vercel. Ikuti urutannya. Jangan bagikan credential di chat, screenshot, Git, atau frontend.

## Yang perlu disiapkan

- Akses ke repository GitHub `Dhede16/keyquiz`, project Supabase, Render, Vercel, dan Groq.
- URL project Supabase, anon/publishable key, service-role key, serta password database. Ambil dari project Supabase yang benar.
- Python 3.12 untuk menjalankan migrasi secara lokal (samakan dengan versi backend di `backend/.python-version`).
- `pg_dump` dan `pg_restore` untuk membuat serta memeriksa backup lokal database.

**Penting:** `SUPABASE_SERVICE_ROLE_KEY` dan `DATABASE_URL` adalah rahasia. Service-role key hanya boleh berada di backend Render. Jangan pernah memakai salah satunya sebagai `VITE_*` atau memasukkannya ke kode frontend.

---

## 1. Pastikan project Supabase yang benar

1. Masuk ke dashboard Supabase dan pilih project KeyQuiz yang memang akan dipakai saat deployment. Pastikan project/ref dan environment-nya benar (production atau staging).
2. Buka bagian **Project Settings → API** (nama menu dapat berubah). Catat Project URL, anon/publishable key, dan service-role/secret key di password manager.
3. Buka **Connect** untuk mendapatkan koneksi PostgreSQL direct atau session pooler dengan SSL. Untuk menjalankan migrasi gunakan direct connection atau session pooler; hindari transaction pooler.
4. Jangan tempelkan password database ke percakapan. Jika password berisi karakter khusus, URL-encode bagian password di connection string.

Kalau belum yakin project mana yang memiliki data penting, berhenti dan pastikan dulu sebelum melanjutkan. Jangan membuat perubahan pada project yang salah.

## 2. Backup dan verifikasi sebelum migrasi

Jangan jalankan migrasi pada database berisi data sebelum backup tersedia. Simpan file backup di lokasi privat **di luar repository** karena isinya dapat memuat data pribadi. `pg_dump` membackup PostgreSQL, bukan isi biner file yang disimpan di Supabase Storage. Jika bucket sudah berisi avatar atau arsip scan yang penting, pastikan file-file itu juga memiliki backup terpisah; jangan menghapus bucket atau objeknya.

Di PowerShell, dari folder repository, gunakan connection string database yang benar:

```powershell
pg_dump --format=custom --file="$env:USERPROFILE\Documents\keyquiz-before-deploy.dump" "<DATABASE_URL>"
pg_restore --list "$env:USERPROFILE\Documents\keyquiz-before-deploy.dump"
```

Ganti `<DATABASE_URL>` dengan connection string direct/session pooler ber-SSL. Pastikan perintah pertama selesai tanpa error dan perintah kedua menampilkan daftar objek backup. Bila `pg_dump`/`pg_restore` belum tersedia, pasang PostgreSQL command-line tools terlebih dahulu atau ikuti prosedur backup yang tersedia untuk paket Supabase Anda. Untuk perubahan berisiko tinggi, uji pemulihan backup ke project/database terpisah; jangan menguji restore ke production.

## 3. Periksa kondisi database lama

Jika Supabase sudah berisi aplikasi/data, pastikan tidak ada deployment atau proses lain yang sedang mengubah profil ketika migrasi dijalankan. Migrasi profil memindahkan `birth_date`, `phone`, dan `gender` ke `profile_private`, lalu menghapus kolom lama dari `profiles`.

Jika kolom `gender` lama mungkin berisi nilai di luar `laki-laki` atau `perempuan`, jalankan query ini di **SQL Editor** sebelum migrasi:

```sql
SELECT id, gender
FROM public.profiles
WHERE gender IS NOT NULL
  AND gender NOT IN ('laki-laki', 'perempuan');
```

Jika ada baris, jangan lanjut dahulu. Tinjau dan normalisasi nilai tersebut dengan pemilik data; jangan menghapus baris untuk memaksa migrasi lewat.

## 4. Siapkan alat migrasi pada Windows

Buka PowerShell di root repository (`keyquiz`). Buat environment Python lokal bila belum ada, lalu pasang dua paket yang diperlukan oleh migration runner:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install python-dotenv psycopg2-binary
```

Jika `.venv` sudah ada dengan Python yang sesuai, tidak perlu membuatnya lagi. Paket backend lengkap tidak perlu dipasang hanya untuk menjalankan migrasi. Jangan menjalankan `database/init_db.py` dari folder lain.

## 5. Terapkan schema dan migrasi

Jalankan runner dari root repository. Masukkan connection string secara tersembunyi saat diminta; jangan simpan di file yang masuk Git:

```powershell
$secure = Read-Host "Masukkan DATABASE_URL (input tidak ditampilkan)" -AsSecureString
$env:DATABASE_URL = [System.Net.NetworkCredential]::new("", $secure).Password
try {
    .\.venv\Scripts\python.exe database\init_db.py
    if ($LASTEXITCODE -ne 0) {
        throw "Migrasi gagal. Baca pesan error di atas; jangan lanjut deploy."
    }
} finally {
    Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
}
```

Runner menerapkan `database/schema.sql` dan file di `database/migrations/` secara berurutan menurut nama, lalu menyimpan versi yang berhasil di `public.keyquiz_schema_migrations`. Jika sebuah file gagal, runner berhenti dan melaporkan nama file; file yang sudah tercatat akan dilewati saat runner dijalankan kembali. Script ini tidak otomatis berjalan saat deploy.

Jalankan query verifikasi berikut di SQL Editor setelah runner melaporkan sukses:

```sql
SELECT version, applied_at
FROM public.keyquiz_schema_migrations
ORDER BY version;
```

Pastikan daftar berisi `000_schema` serta versi migrasi yang tersedia di folder `database/migrations/`, termasuk migrasi terbaru. Pastikan juga tabel `profile_private` ada:

```sql
SELECT to_regclass('public.profile_private') AS profile_private_table;
```

Hasil `profile_private_table` harus `profile_private` (atau `public.profile_private`, tergantung tampilan SQL Editor). Jika runner gagal, catat nama file migrasi dan pesan error, jangan deploy kode baru dan jangan menghapus tabel/riwayat migrasi. Perbaiki kondisi yang disebut error, ambil bantuan jika tidak jelas, lalu jalankan runner lagi; versi yang sudah tercatat akan dilewati.

### Jika koneksi langsung dari komputer tidak tersedia

Gunakan SQL Editor hanya bila memahami bahwa setiap file harus dijalankan **satu per satu dan tetap berurutan**:

1. Jalankan `database/schema.sql`.
2. Jalankan setiap `.sql` di `database/migrations/` menurut urutan nama.
3. Berhenti saat ada error; jangan lanjutkan ke file berikutnya.
4. Setelah semua file sukses, catat versi yang memang sudah berhasil agar migration runner tidak menjalankannya lagi. Jangan masukkan versi file yang gagal atau belum dijalankan.

Contoh pencatatan setelah baseline dan **semua** migrasi sukses:

```sql
INSERT INTO public.keyquiz_schema_migrations (version)
VALUES
    ('000_schema'),
    ('20261004_scanned_results_student_privacy'),
    ('20261005_remove_profile_plaintext_password'),
    ('20261006_profile_columns'),
    ('20261006_profile_storage'),
    ('20261006_scanned_sheet_archives'),
    ('20261013_foreign_key_indexes'),
    ('20261013_profile_private')
ON CONFLICT (version) DO NOTHING;
```

Sesuaikan daftar dengan nama file yang benar-benar dijalankan. Jika sebelumnya pernah menerapkan migrasi manual atau statusnya tidak diketahui, **jangan jalankan pencatatan contoh secara membabi buta**. Periksa schema dan riwayat dahulu. Untuk menghindari pencatatan ganda yang keliru, cara yang disarankan tetap menjalankan `database/init_db.py`.

## 6. Periksa pengaturan Supabase untuk aplikasi

### Authentication

1. Buka **Authentication → URL Configuration**.
2. Set **Site URL** ke alamat production frontend Vercel, misalnya `https://nama-proyek.vercel.app`.
3. Tambahkan alamat tersebut ke daftar **Redirect URLs** bila alur auth/email membutuhkannya. Tambahkan domain kustom hanya jika benar-benar digunakan.
4. Simpan. Jangan memasukkan wildcard redirect yang tidak diperlukan.

### Storage dan keamanan database

1. Pastikan bucket `profile` dan `scan-archives` tersedia setelah migrasi.
2. Sesuai schema aplikasi, `profile` menyimpan avatar publik; `scan-archives` bersifat privat. Jangan mengubah bucket arsip menjadi public.
3. Kebijakan tabel dan Storage dibuat/diatur oleh SQL schema/migrasi. Jangan menonaktifkan RLS atau menghapus policy untuk mengatasi error akses; periksa error dan policy yang bersangkutan.
4. Jangan membuat ulang project, menghapus Auth users, tabel, bucket, atau objek Storage sebagai langkah perbaikan.

## 7. Siapkan domain Vercel dan deploy backend ke Render

1. Pastikan perubahan aplikasi/migrasi yang memang ingin dirilis sudah di-push ke branch GitHub yang akan di-deploy. Dari PowerShell di root repo, tinjau working tree lalu stage file rilis secara eksplisit:

   ```powershell
   git status --short
   git add README.md .env.example backend/app/main.py backend/.python-version database/init_db.py database/schema.sql database/migrations/20261013_foreign_key_indexes.sql database/migrations/20261013_profile_private.sql frontend/src/composables/useAuth.js frontend/src/services/api.js frontend/src/services/supabase.js frontend/.env.example frontend/vercel.json render.yaml step.md
   git diff --cached --check
   git diff --cached
   ```

   Pastikan staged diff hanya berisi perubahan yang memang akan dirilis. Jangan commit `.env`, backup database, atau key rahasia. Jangan gunakan `git add -A` jika ada pekerjaan lain di working tree. Setelah meninjau diff:

   ```powershell
   git commit -m "Prepare KeyQuiz for production deployment"
   git push origin <branch>
   ```

   Ganti `<branch>` dengan branch Git yang dipilih sebagai branch production di Vercel dan Render.
2. Buat/import project Vercel untuk repository ini dan pilih **Root Directory** `frontend`. Catat domain production yang diberikan Vercel; deployment frontend dapat dilakukan setelah URL backend tersedia.
3. Buat Blueprint/layanan Render dari repository menggunakan `render.yaml`. Pastikan pengaturannya terdeteksi:
   - Root directory: `backend`
   - Plan: `Standard` (pastikan biaya paket sesuai sebelum konfirmasi)
   - Health check: `/`
   - Persistent disk: `/var/data`
   - `CHROMA_DB_PATH` dan `HF_HOME` berada di `/var/data`
4. Isi environment variables di Render:

   | Nama | Nilai |
   |---|---|
   | `SUPABASE_URL` | Project URL Supabase |
   | `SUPABASE_ANON_KEY` | Anon/publishable key project |
   | `SUPABASE_SERVICE_ROLE_KEY` | Service-role/secret key; rahasia backend |
   | `GROQ_API_KEY` | API key Groq |
   | `CORS_ORIGINS` | Domain frontend Vercel persis, tanpa trailing slash |

   `CHROMA_DB_PATH` dan `HF_HOME` sudah didefinisikan oleh `render.yaml`. Jangan mengisi `DATABASE_URL` di Render—migration runner dijalankan oleh operator, bukan saat aplikasi hidup.
5. Deploy backend. Tunggu status deploy dan health check sukses. Simpan base URL service, misalnya `https://keyquiz-api.onrender.com`.
6. Tes `https://<service>.onrender.com/`. Respons harus berisi status online sebelum melanjutkan.

## 8. Deploy frontend ke Vercel

Di **Project Settings → Environment Variables** Vercel, isi untuk environment Production:

| Nama | Nilai |
|---|---|
| `VITE_SUPABASE_URL` | Project URL Supabase |
| `VITE_SUPABASE_ANON_KEY` | Anon/publishable key Supabase |
| `VITE_API_BASE_URL` | URL backend Render + `/api`, contoh `https://keyquiz-api.onrender.com/api` |

Jangan menambahkan `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`, atau `GROQ_API_KEY` ke Vercel. Jalankan deployment production. Jika environment variable diubah setelah build, lakukan redeploy agar frontend dibangun ulang dengan nilai baru.

## 9. Kunci CORS ke domain yang benar

1. Salin origin production Vercel persis, misalnya `https://nama-proyek.vercel.app` (tanpa `/` di akhir dan tanpa path).
2. Pastikan nilai `CORS_ORIGINS` di Render hanya memuat domain yang dipercaya. Jangan gunakan `*`.
3. Jika memakai domain kustom, masukkan origin kustom yang aktif juga; pisahkan beberapa origin dengan koma.
4. Simpan perubahan dan redeploy/restart backend.

## 10. Uji aplikasi yang sudah live

Gunakan akun uji dan data yang aman:

- Buka situs Vercel, daftar akun uji, lalu login/logout.
- Periksa bahwa profil dan daftar kelas yang sesuai dapat dimuat; uji pembaruan profil/avatar.
- Uji pembuatan tugas dan pengumpulan jawaban sesuai peran pengajar/mahasiswa.
- Uji pembuatan kuis AI, scan jika layanan vision sudah dikonfigurasi, dan penilaian esai.
- Periksa bahwa mahasiswa hanya melihat hasil scan yang ditujukan kepadanya.
- Periksa log Render dan tab Network/Console browser bila request gagal.
- Setelah satu restart/redeploy backend, pastikan vector data/cache yang diharapkan tetap ada melalui disk persisten Render.

Deployment dianggap siap setelah URL health check sehat, frontend tidak memiliki error konfigurasi/CORS, dan alur inti yang diperlukan berhasil.

## Jika terjadi masalah

- **Migration runner gagal:** jangan deploy; simpan nama file dan pesan error. Backup jangan dihapus. Jangan menghapus entry di `keyquiz_schema_migrations` tanpa mengetahui efeknya.
- **Gender tidak valid:** gunakan query pada langkah 3, sepakati normalisasi dengan pemilik data, lalu ulangi migrasi.
- **Frontend menampilkan error konfigurasi:** periksa tiga variabel `VITE_*` di Vercel dan redeploy.
- **Request API gagal/CORS:** periksa `VITE_API_BASE_URL`, `CORS_ORIGINS`, origin tanpa slash, lalu log Render; setelah mengubah env, redeploy layanan terkait.
- **Supabase menolak akses:** periksa apakah migrasi sukses, user sedang login ke project yang benar, dan RLS/policy sesuai. Jangan mematikan RLS sebagai jalan pintas.
- **Perlu pemulihan:** lakukan dari backup yang sudah diverifikasi mengikuti prosedur restore yang tepat. Jangan menjalankan restore ke production tanpa memastikan target database dan dampak penggantian data.

## Referensi repo

- [Skema database](database/schema.sql)
- [Migration runner](database/init_db.py)
- [Daftar migrasi](database/migrations/)
- [Environment backend](.env.example)
- [Environment frontend](frontend/.env.example)
- [Blueprint Render](render.yaml)
- [Konfigurasi Vercel](frontend/vercel.json)
