# Penjelasan Alur KeyQuiz

Dokumen ini dapat digunakan sebagai panduan presentasi tentang alur sistem, cara penilaian pilihan ganda dan esai, serta fitur pemindaian lembar jawaban.

## 1. Gambaran umum sistem

KeyQuiz menghubungkan antarmuka web dengan layanan backend untuk membantu dosen membuat tugas, menerima jawaban, dan melakukan penilaian.

```text
Dosen membuat tugas / scan lembar
              │
              ▼
      Antarmuka KeyQuiz
              │
              ├── Jawaban pilihan ganda ──► cocokkan dengan kunci
              ├── Jawaban esai ───────────► AI menilai rubrik
              └── Foto lembar ────────────► Vision AI membaca isi
                                               │
                                               ▼
                                    Dosen memeriksa hasil
                                               │
                                               ▼
                                  Nilai dikirim dan disimpan
```

AI membantu membaca atau memberi penilaian awal. Dosen tetap dapat meninjau hasil dan mengoreksi nilai sebelum hasil scan dibagikan.

## 2. Alur pengerjaan tugas oleh mahasiswa

1. Dosen menyiapkan tugas beserta soal, kunci jawaban, bobot, dan rubrik bila soalnya esai.
2. Mahasiswa membuka tugas di kelas dan mengisi jawaban.
3. Saat jawaban dikirim, sistem menilai setiap soal:
   - Pilihan ganda dinilai dengan mencocokkan jawaban terhadap kunci.
   - Esai dikirim ke layanan penilaian AI berdasarkan rubrik.
4. Jawaban, nilai per soal, serta hasil evaluasi esai disertakan pada pengumpulan tugas.
5. Dosen dapat membuka hasil pengumpulan, meninjau rincian penilaian, lalu mengirim nilai akhir. Status tugas berubah menjadi sudah dinilai.

## 3. Cara sistem menilai pilihan ganda

Pilihan ganda dinilai dengan **pencocokan langsung**, bukan dengan penilaian pemahaman oleh AI.

- Jawaban mahasiswa dinormalisasi (spasi tepi dihapus dan huruf tidak dibedakan).
- Jika jawabannya sama dengan kunci, mahasiswa memperoleh bobot penuh soal tersebut.
- Jika berbeda atau kosong, nilai soal adalah 0.
- Nilai akhir adalah penjumlahan nilai soal, dengan nilai maksimum mengikuti total bobot tugas.

**Contoh:** soal berbobot 10 poin. Jawaban yang cocok dengan kunci mendapat 10; jawaban yang salah atau tidak diisi mendapat 0.

## 4. Cara sistem menilai esai

Penilaian esai menggunakan kunci jawaban acuan dan rubrik. AI boleh menerima jawaban dengan susunan kalimat berbeda selama konsepnya sesuai.

```text
Jawaban mahasiswa
        │
        ├── Dibuat menjadi embedding teks
        │       └── ChromaDB mencari kunci untuk soal yang sama
        │           dan menghitung similarity sebagai konteks
        │
        └── Soal + kunci + rubrik + jawaban
                └── LLM memberi skor pada setiap kriteria
                    serta alasan dan bukti kutipan
```

Cara menghitung nilai:

1. AI memberi skor untuk setiap kriteria rubrik pada rentang **0 sampai 1**:
   - `0` = tidak terpenuhi atau salah.
   - Nilai di antara 0 dan 1 = terpenuhi sebagian.
   - `1` = terpenuhi dengan benar.
2. Semua kriteria memiliki bobot yang sama. Nilai AI adalah rata-rata skor kriteria dikali 100.
3. Nilai AI pada skala 0–100 dikonversi ke bobot poin soal. Contohnya, skor AI 80 untuk soal berbobot 10 menjadi 8 poin.
4. Hasil menyertakan alasan, skor dan status tiap kriteria, serta kutipan bukti jika kutipan benar-benar muncul dalam jawaban mahasiswa.
5. Jika rubrik tidak tersedia, sistem memakai satu kriteria umum berdasarkan kunci jawaban.
6. Jawaban kosong langsung mendapat nilai 0 tanpa pemanggilan embedding atau LLM.

**Catatan penting:** similarity embedding hanya menjadi informasi konteks yang dikembalikan bersama hasil. Pada implementasi saat ini, nilai akhir esai dihitung dari rata-rata skor rubrik, bukan dari persentase similarity.

## 5. Cara kerja fitur scan

Fitur scan pada halaman **Scan Soal** ditujukan untuk lembar pilihan ganda yang berisi teks soal, opsi, dan tanda jawaban siswa.

1. Dosen mengunggah foto JPG, PNG, atau WEBP. Batas ukuran foto adalah 10 MB.
2. Backend memperbaiki orientasi foto, mengubahnya menjadi JPEG, dan mengecilkan sisi terpanjang hingga maksimum 1600 piksel.
3. Vision AI membaca foto dan mengembalikan data terstruktur, antara lain:
   - Nomor dan teks soal.
   - Huruf serta teks opsi.
   - Opsi yang ditandai siswa.
   - Saran kunci jawaban dan bobot soal.
   - Penanda tingkat keyakinan pembacaan jawaban dan saran kunci.
4. Backend merapikan hasil, mengabaikan jawaban yang tidak sesuai dengan opsi yang terbaca, dan menormalkan bobot agar totalnya tepat 100 poin.
5. Sistem menghitung nilai awal per soal: jawaban terbaca yang sama dengan saran kunci memperoleh bobot soal; selain itu mendapat 0.
6. Dosen memeriksa dan dapat mengoreksi teks, jawaban siswa, kunci, bobot, serta nilai. Kunci untuk tiap soal harus dipilih dan total bobot harus tepat 100 sebelum hasil dapat dikirim.
7. Dosen memilih kelas dan mahasiswa tujuan. Hasil scan disimpan sebagai tugas di kelas; foto dan koreksi dapat disimpan pada arsip kelas.

### Scan esai

Backend juga menyediakan jenis scan esai untuk menyalin jawaban tulisan tangan menjadi teks per nomor soal. Hasilnya adalah transkripsi—bukan nilai esai otomatis. Penilaian esai dilakukan melalui alur penilaian rubrik, dengan soal, kunci, dan rubrik yang sesuai. Halaman **Scan Soal** saat ini menjalankan alur pilihan ganda.

## 6. Pembuatan soal dengan AI

Dosen dapat memberikan instruksi seperti topik, jumlah, dan tipe soal. AI menghasilkan paket soal beserta kunci; soal esai juga dapat dilengkapi rubrik. Bobot yang dibuat diminta berjumlah tepat 100. Dosen tetap perlu meninjau isi, kunci, dan bobot sebelum membagikan tugas.

Pembuatan soal ini berbeda dari penilaian: AI generator menyusun materi soal, sedangkan penilaian pilihan ganda menggunakan pencocokan kunci dan penilaian esai menggunakan evaluasi rubrik.

## 7. Hal yang perlu disampaikan saat presentasi

- **Pilihan ganda:** cepat dan konsisten karena memakai pencocokan kunci serta bobot soal.
- **Esai:** AI menilai pemenuhan tiap kriteria, bukan sekadar mencari kalimat yang sama dengan kunci.
- **Scan:** Vision AI membantu mengubah lembar foto menjadi data yang dapat diperiksa dan dikoreksi.
- **Kendali dosen:** hasil scan adalah penilaian awal; dosen memeriksa bacaan, kunci, bobot, dan nilai sebelum mengirimkannya.
- **Batas akurasi:** kualitas foto, tulisan tangan, tanda pilihan yang ambigu, atau kunci/rubrik yang kurang tepat dapat memengaruhi hasil. Pemeriksaan manusia tetap penting.

### Naskah singkat

> “KeyQuiz memiliki tiga alur utama. Untuk pilihan ganda, sistem membandingkan jawaban mahasiswa dengan kunci dan memberi bobot penuh jika cocok. Untuk esai, AI menilai setiap kriteria rubrik dengan skor 0 sampai 1, lalu merata-ratakannya menjadi nilai soal; similarity teks hanya menjadi konteks tambahan. Untuk lembar kertas, Vision AI membaca soal dan tanda jawaban dari foto, kemudian sistem membuat nilai awal. Dosen memeriksa dan mengoreksi hasil scan sebelum mengirimkannya kepada mahasiswa.”
