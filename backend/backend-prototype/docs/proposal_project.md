**PENGEMBANGAN SISTEM PENILAIAN ESAI BERBASIS ARTIFICIAL INTELLIGENCE UNTUK MENGURANGI SUBJEKTIVITAS DALAM EVALUASI JAWABAN MAHASISWA**

Disusun oleh:

**BORNEO IT**

Anggota:

Dhede Febrian Purnawiranto Ketua 256151011

Affan Anggota 256151002

Winner Anggota 256151025

**SOFTWARE DEVELOPMENT COMPETITION**

**ICONFEST**

**2026**

# **KATA PENGANTAR**

Puji syukur kami panjatkan ke hadirat Tuhan Yang Maha Esa atas limpahan rahmat dan karunia-Nya sehingga kami dapat menyelesaikan laporan project yang berjudul "Pengembangan Sistem Penilaian Esai Berbasis _Artificial Intelligence_ untuk Mengurangi Subjektivitas dalam Evaluasi Jawaban Mahasiswa".

Laporan ini disusun sebagai bagian dari keikutsertaan kami dalam _Software Development Competition_ pada ajang ICONFEST 2026. Laporan ini memuat latar belakang, deskripsi project, perancangan dan implementasi, serta hasil pengembangan aplikasi KeyQuiz, yaitu sistem penilaian esai berbasis _Artificial Intelligence_ yang dirancang untuk membantu dosen menilai jawaban mahasiswa secara lebih objektif, konsisten, dan efisien.

Kami mengucapkan terima kasih kepada panitia ICONFEST 2026 yang telah menyelenggarakan kompetisi ini, kepada Bapak Muhammad Taufiq Sumadi, S.Tr.Kom., M.Tr.Kom dan Politeknik Negeri Samarinda yang telah memberikan bimbingan dan dukungan, serta kepada seluruh pihak yang telah membantu penyusunan laporan ini.

Kami menyadari bahwa laporan ini masih memiliki keterbatasan. Oleh karena itu, kritik dan saran yang membangun sangat kami harapkan demi perbaikan di masa mendatang. Semoga laporan ini bermanfaat bagi pembaca dan bagi pengembangan teknologi pendidikan.

Samarinda, tanggal 2026

Tim Borneo IT

**DAFTAR ISI**

**KATA PENGANTAR 2**

**ABSTRAK 4**

**BAB I PENDAHULUAN 5**

1.1 Latar Belakang 5

1.2 Rumusan Masalah 6

1.3 Tujuan Project 6

1.4 Manfaat Project 7

1.5 Batasan Masalah 8

**BAB II DESKRIPSI PROJECT 9**

2.1 Deskripsi Project 9

2.2 Permasalahan dan Urgensi Project 9

2.3 Solusi yang Ditawarkan 10

2.4 Keunggulan dan Nilai Inovasi 11

**BAB III PERANCANGAN DAN IMPLEMENTASI PROJECT 13**

3.1 Konsep dan Alur Project 13

3.2 Target Pengguna dan Potensi Pasar 16

3.3 Perancangan Project 17

3.4 Teknologi yang Digunakan 18

3.5 Prototype dan Implementasi 19

**BAB IV HASIL DAN PEMBAHASAN 21**

4.1 Hasil Project 21

4.2 Fitur dan Fungsionalitas 21

4.3 Pengujian 22

**BAB V PENUTUP 23**

5.1 Kesimpulan 23

5.2 Saran 23

**DAFTAR PUSTAKA 25**

# **ABSTRAK**

Penilaian jawaban esai secara manual masih menjadi praktik umum di perguruan tinggi, tetapi bersifat subjektif, memerlukan waktu yang besar, dan berpotensi menghasilkan nilai yang tidak konsisten, baik antar dosen maupun antar lembar jawaban mahasiswa. Project ini bertujuan mengembangkan KeyQuiz, sebuah sistem penilaian esai berbasis Artificial Intelligence yang membantu dosen menilai jawaban mahasiswa secara lebih objektif, konsisten, dan efisien.

Sistem membandingkan jawaban mahasiswa dengan kunci jawaban atau rubrik berdasarkan kemiripan makna (semantic similarity) menggunakan representasi text embedding yang disimpan pada basis data vektor, dengan bantuan model bahasa untuk menganalisis jawaban yang kemiripannya berada pada rentang menengah; koreksi esai otomatis ini menjadi fitur unggulan KeyQuiz. Selain itu, sistem menyediakan pembuatan tugas otomatis oleh AI (pilihan ganda atau esai beserta kunci jawaban) yang dapat dikirim dosen ke kelas untuk dikerjakan mahasiswa melalui akun masing-masing, pemindaian jawaban dari lembar kertas sebagai fitur pendukung, serta dashboard nilai dan performa mahasiswa. Sistem dibangun sebagai aplikasi web dengan Vue.js pada sisi antarmuka, FastAPI pada sisi server, serta Supabase dan ChromaDB pada sisi penyimpanan data. Sistem diposisikan sebagai alat bantu, nilai dari AI dapat ditinjau dan diubah oleh dosen sehingga keputusan akhir tetap berada pada dosen.

Kata kunci: penilaian esai, Artificial Intelligence, semantic similarity, text embedding, subjektivitas penilaian

# **BAB I

PENDAHULUAN**

## **1.1 Latar Belakang**

Evaluasi pembelajaran merupakan bagian penting dalam proses pendidikan untuk mengukur sejauh mana mahasiswa memahami materi yang telah diajarkan. Salah satu bentuk evaluasi yang sering digunakan di perguruan tinggi adalah soal esai. Berbeda dengan soal pilihan ganda, soal esai menuntut mahasiswa menjelaskan konsep dengan bahasa sendiri, sehingga lebih mampu menunjukkan kedalaman pemahaman, kemampuan analisis, dan kemampuan bernalar.

Namun, penilaian jawaban esai masih dilakukan secara manual oleh dosen atau pengajar. Cara ini memiliki beberapa kelemahan. Pertama, penilaian bersifat subjektif. Dua penilai yang berbeda dapat memberikan nilai yang berbeda untuk jawaban yang sama, dan penilai yang sama pun dapat tidak konsisten karena faktor kelelahan, suasana hati, urutan lembar jawaban, atau kesan terhadap mahasiswa tertentu. Kedua, penilaian manual memerlukan waktu dan tenaga yang besar, terutama pada kelas dengan jumlah mahasiswa banyak. Ketiga, umpan balik kepada mahasiswa sering terlambat sehingga kurang efektif untuk perbaikan belajar.

Perkembangan Artificial Intelligence (AI), khususnya Natural Language Processing (NLP), membuka peluang untuk mengatasi masalah tersebut. Teknik seperti text embedding dan semantic similarity memungkinkan komputer mengukur kemiripan makna antara dua teks, bukan hanya kesamaan kata. Dengan teknik ini, jawaban mahasiswa dapat dibandingkan dengan kunci jawaban atau rubrik penilaian berdasarkan makna, sehingga jawaban yang menggunakan kalimat berbeda tetapi maksudnya benar tetap dapat dinilai dengan tepat. Selain itu, Large Language Model (LLM) dapat dimanfaatkan untuk membantu menganalisis jawaban dan meluruskan jawaban yang bermakna sama tetapi berbeda susunan katanya, sehingga jawaban tersebut tetap memperoleh nilai yang sesuai.

Penggunaan sistem penilaian berbasis AI diharapkan dapat menerapkan kriteria yang sama untuk setiap jawaban, sehingga hasil penilaian lebih konsisten dan objektif. Sistem ini juga dapat mempercepat proses penilaian, sehingga dosen memiliki lebih banyak waktu untuk kegiatan pembelajaran lainnya. Meski demikian, sistem ini diposisikan sebagai alat bantu, dan keputusan akhir tetap berada di tangan dosen.

Berdasarkan uraian tersebut, diperlukan pengembangan sistem penilaian esai berbasis Artificial Intelligence yang mampu membandingkan jawaban mahasiswa dengan kunci jawaban atau rubrik secara semantik. Sistem ini diharapkan dapat mengurangi subjektivitas, meningkatkan konsistensi dan efisiensi penilaian, serta membantu dosen dalam mengevaluasi jawaban mahasiswa secara lebih adil dan transparan.

## **1.2 Rumusan Masalah**

Berdasarkan latar belakang yang telah diuraikan, rumusan masalah dalam pengembangan sistem ini adalah sebagai berikut:

1. Bagaimana subjektivitas penilai memengaruhi hasil penilaian jawaban esai mahasiswa sehingga menimbulkan ketidakkonsistenan nilai?
2. Mengapa penilaian esai secara manual kurang efektif dan efisien, terutama pada jumlah mahasiswa yang banyak?
3. Bagaimana mengembangkan sistem penilaian esai berbasis Artificial Intelligence yang dapat mengurangi subjektivitas serta membantu dosen menilai jawaban mahasiswa secara lebih objektif, konsisten, dan efisien?

## **1.3 Tujuan Project**

### 1.3.1 Tujuan Umum

Mengembangkan sistem penilaian esai berbasis Artificial Intelligence yang mampu mengurangi subjektivitas dalam evaluasi jawaban mahasiswa.

### 1.3.2 Tujuan Khusus

1. Merancang dan membangun sistem yang membandingkan jawaban mahasiswa dengan kunci jawaban atau rubrik berdasarkan kemiripan makna.
2. Menyediakan fitur pembuatan tugas otomatis dengan bantuan AI, pengerjaan tugas oleh mahasiswa di dalam kelas, serta dashboard nilai dan performa, dengan fitur pendukung berupa pemindaian jawaban dari kertas.
3. Meningkatkan konsistensi, kecepatan, dan transparansi proses penilaian esai dengan tetap menempatkan dosen sebagai pengambil keputusan akhir.

## **1.4 Manfaat Project**

Manfaat yang diharapkan dari pengembangan project ini adalah sebagai berikut:

1. Bagi dosen atau pengajar: mengurangi beban dan waktu koreksi, mempercepat pembuatan tugas beserta kunci jawabannya, serta membantu menerapkan kriteria penilaian yang seragam pada seluruh jawaban.
2. Bagi mahasiswa: memperoleh penilaian yang lebih adil dan konsisten, mengerjakan tugas serta memantau nilai melalui akun sendiri, dan berpeluang menerima umpan balik dengan lebih cepat.
3. Bagi institusi pendidikan: mendukung digitalisasi proses asesmen dan meningkatkan kualitas serta akuntabilitas evaluasi pembelajaran.
4. Bagi pengembang dan dunia akademik: menjadi contoh penerapan NLP dan AI pada bidang pendidikan yang dapat dikembangkan lebih lanjut.

## **1.5 Batasan Masalah**

Agar pengembangan lebih terarah, project ini memiliki batasan sebagai berikut:

1. Sistem berfokus pada penilaian jawaban esai berbasis teks, baik yang dikerjakan langsung oleh mahasiswa pada halaman pengerjaan di sistem maupun yang diperoleh dari hasil pemindaian lembar jawaban.
2. Kunci jawaban atau rubrik penilaian disusun oleh dosen atau dihasilkan AI bersama tugas, dan digunakan sebagai acuan penilaian.
3. Penilaian difokuskan pada kesesuaian makna jawaban terhadap kunci jawaban atau rubrik.
4. Sistem berfungsi sebagai alat bantu, nilai dari AI dapat ditinjau dan diubah oleh dosen sehingga keputusan nilai akhir tetap berada pada dosen.

# **BAB II

DESKRIPSI PROJECT**

## **2.1 Deskripsi Project**

KeyQuiz adalah aplikasi web penilaian esai berbasis Artificial Intelligence yang dikembangkan oleh Tim Borneo IT. Aplikasi ini membantu dosen atau pengajar menilai jawaban esai mahasiswa dengan membandingkan jawaban tersebut terhadap kunci jawaban atau rubrik penilaian berdasarkan kemiripan makna, bukan sekadar kesamaan kata.

Secara umum, dosen membuat kelas dan tugas, baik secara manual maupun dengan bantuan AI yang menghasilkan soal (pilihan ganda atau esai) beserta kunci jawabannya. Tugas yang telah siap dikirim ke kelas, kemudian mahasiswa mengerjakannya melalui akun KeyQuiz pada halaman pengerjaan. Sistem menghitung tingkat kesesuaian makna jawaban terhadap kunci jawaban dan menghasilkan nilai yang dapat ditinjau dan diubah oleh dosen. Apabila tugas dikerjakan di atas kertas, dosen cukup memindai lembar jawaban sehingga soal dan jawaban tampil pada sistem, dinilai, dan hasilnya dikirim ke kelas sebagai tugas yang telah selesai. Nilai tampil pada dashboard mahasiswa sehingga perkembangan performa dapat dipantau.

Fitur unggulan KeyQuiz adalah koreksi esai otomatis berbasis AI, sedangkan pemindaian jawaban kertas berperan sebagai fitur pendukung bagi tugas yang dikerjakan secara manual.

## **2.2 Permasalahan dan Urgensi Project**

### 2.2.1 Permasalahan

Penilaian esai secara manual menghadapi beberapa permasalahan utama, yaitu:

1. Subjektivitas penilai. Nilai dapat dipengaruhi oleh kelelahan, suasana hati, urutan lembar jawaban yang diperiksa, serta kesan penilai terhadap mahasiswa. Akibatnya, jawaban dengan kualitas serupa dapat memperoleh nilai berbeda.
2. Ketidak konsistenan antar dosen dalam menilai. Ketika beberapa dosen atau asisten memeriksa jawaban pada mata kuliah yang sama, tafsir terhadap kunci jawaban dan rubrik dapat berbeda.
3. Beban waktu dan tenaga. Membaca dan menilai jawaban esai satu per satu memerlukan waktu yang jauh lebih lama dibandingkan soal pilihan ganda, terutama pada kelas besar.
4. Umpan balik yang lambat. Hasil penilaian yang terlambat diterima mengurangi kesempatan mahasiswa untuk memperbaiki pemahaman.

### 2.2.2 Urgensi

Pengembangan sistem ini penting dilakukan karena keadilan dan objektivitas penilaian berdampak langsung pada mahasiswa, sedangkan beban koreksi manual terus meningkat seiring bertambahnya jumlah peserta didik. Di sisi lain, kemajuan NLP dan Large Language Model telah membuat pemahaman makna teks oleh komputer jauh lebih baik dibandingkan pendekatan pencocokan kata kunci. Gagasan penilaian esai oleh komputer sendiri telah dikaji sejak lama, dan teknologi saat ini memungkinkan penerapannya secara lebih praktis dan mudah diakses melalui aplikasi web.

## **2.3 Solusi yang Ditawarkan**

KeyQuiz menawarkan solusi berupa penilaian esai yang dibantu AI dengan pendekatan sebagai berikut:

1. Penilaian berbasis makna. Kunci jawaban dan jawaban mahasiswa diubah menjadi representasi vektor (embedding), lalu tingkat kemiripan maknanya dihitung. Pendekatan ini sejalan dengan model representasi kalimat seperti Sentence-BERT. Model bahasa Qwen membantu menganalisis dan meluruskan jawaban yang kemiripannya berada pada rentang menengah, sehingga jawaban yang bermakna sama tetapi berbeda susunan katanya tetap memperoleh nilai yang sesuai.
2. Kriteria yang seragam. Seluruh jawaban dibandingkan dengan acuan yang sama sehingga konsistensi penilaian meningkat.
3. Pembuatan tugas otomatis dengan AI. Large Language Model membantu dosen membuat tugas berupa soal pilihan ganda atau esai beserta kunci jawabannya, sehingga tugas siap dikirim ke kelas dan dikerjakan mahasiswa melalui akun masing-masing.
4. Pemindaian jawaban (fitur pendukung). Untuk tugas yang dikerjakan di kertas, dosen memindai lembar jawaban, soal dan jawaban tampil pada sistem, dinilai, dan dapat dikoreksi dosen sebelum hasilnya dikirim ke kelas.
5. Dashboard performa. Nilai dan perkembangan mahasiswa disajikan dalam satu tampilan untuk memudahkan pemantauan.
6. Dosen sebagai penentu akhir. Nilai dari sistem, baik dari jawaban yang dikerjakan langsung maupun hasil pemindaian, berfungsi sebagai rekomendasi yang dapat ditinjau dan diubah oleh dosen.

## **2.4 Keunggulan dan Nilai Inovasi**

Keunggulan dan nilai inovasi KeyQuiz dibandingkan penilaian manual dirangkum pada Tabel 2.1.

Tabel 2.1 Perbandingan Penilaian Manual dan KeyQuiz

| **Aspek**        | **Penilaian Manual**                                    | **KeyQuiz**                                                       |
| ---------------- | ------------------------------------------------------- | ----------------------------------------------------------------- |
| Konsistensi      | Dipengaruhi kelelahan, suasana hati, dan urutan koreksi | Menggunakan acuan dan cara hitung yang sama untuk setiap jawaban  |
| Objektivitas     | Rentan terhadap kesan terhadap mahasiswa                | Menilai berdasarkan kesesuaian makna terhadap kunci jawaban       |
| Kecepatan        | Lambat pada jumlah mahasiswa banyak                     | Penilaian otomatis dan lebih cepat                                |
| Pembuatan tugas  | Soal dan kunci jawaban disusun manual                   | AI membuat soal (pilihan ganda atau esai) beserta kunci jawaban   |
| Input jawaban    | Dibaca langsung dari kertas                             | Dikerjakan mahasiswa langsung di sistem atau dipindai dari kertas |
| Pemantauan hasil | Rekap nilai dilakukan manual                            | Nilai dan performa tersaji pada dashboard                         |

Nilai inovasi KeyQuiz terletak pada beberapa hal berikut:

- Pemahaman makna, bukan pencocokan kata kunci, sehingga jawaban dengan susunan kalimat berbeda tetapi bermakna benar tetap dapat dinilai.
- Integrasi penilaian esai, pembuatan tugas, pengerjaan tugas di dalam kelas, pemindaian jawaban, dan dashboard dalam satu aplikasi.
- Pendekatan human-in-the-loop, yaitu AI membantu memberi nilai, sedangkan dosen dapat meninjau dan mengubah nilai sebagai penentu akhir.
- Arsitektur berbasis web yang mudah diakses tanpa instalasi khusus pada perangkat pengguna.

# **BAB III

PERANCANGAN DAN IMPLEMENTASI PROJECT**

## **3.1 Konsep dan Alur Project**

Konsep utama KeyQuiz adalah menjadikan kunci jawaban sebagai acuan tetap yang dibandingkan dengan setiap jawaban mahasiswa berdasarkan makna. Alur kerja sistem ditunjukkan pada Gambar 3.1 dan terdiri atas dua jalur, yaitu jalur digital sebagai jalur utama dan jalur kertas sebagai jalur pendukung.

**Jalur digital (utama):**

1. Dosen masuk ke sistem, membuat kelas, lalu membuat tugas (pilihan ganda atau esai) beserta kunci jawaban atau rubrik, baik secara manual maupun dengan bantuan AI.
2. Kunci jawaban esai diubah menjadi embedding dan disimpan pada basis data vektor (ChromaDB).
3. Dosen mengirim tugas ke kelas.
4. Mahasiswa masuk dengan akun KeyQuiz dan mengerjakan tugas pada halaman pengerjaan di dalam kelas.
5. Jawaban mahasiswa diubah menjadi embedding, lalu sistem menghitung kemiripan makna antara jawaban dan kunci jawaban dan menghasilkan skor.
6. Untuk jawaban yang kemiripannya berada pada rentang menengah, model bahasa Qwen menganalisis jawaban dan meluruskannya terhadap kunci jawaban, sehingga jawaban yang bermakna sama tetapi berbeda susunan katanya tetap memperoleh nilai yang sesuai. Hasil analisis ini tidak ditampilkan sebagai penjelasan kepada mahasiswa.
7. Dosen meninjau nilai dari AI dan dapat mengubahnya.
8. Nilai tersimpan dan ditampilkan pada dashboard mahasiswa.

**Jalur kertas (pendukung):**

1. Dosen membuat dan mengirim tugas ke kelas seperti pada jalur digital.
2. Tugas dikerjakan di atas kertas dan dikumpulkan kepada dosen.
3. Dosen memindai (scan) lembar jawaban.
4. Sistem membaca jawaban dan menilainya berdasarkan kunci jawaban menggunakan kemiripan makna, dengan bantuan analisis Qwen untuk jawaban yang kemiripannya berada pada rentang menengah.
5. Soal dan jawaban tampil pada antarmuka, dan dosen dapat mengoreksi atau mengubahnya.
6. Hasil dikirim ke kelas sebagai tugas yang telah selesai, dan nilai ditampilkan pada dashboard mahasiswa.

Gambar 3.1 Alur Kerja Sistem KeyQuiz (Jalur Digital dan Jalur Kertas)

## **3.2 Target Pengguna dan Potensi Pasar**

### 3.2.1 Target Pengguna

Pengguna KeyQuiz terdiri atas dosen atau pengajar yang mengelola kelas dan tugas, serta mahasiswa atau peserta didik yang mengerjakan tugas dan memantau nilai. Target pengguna KeyQuiz dirangkum pada Tabel 3.1.

Tabel 3.1 Target Pengguna KeyQuiz

| **Segmen Pengguna**                       | **Kebutuhan**                                                                                                                           |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Dosen perguruan tinggi                    | Membuat kelas dan tugas (dibantu AI), menilai jawaban esai dengan cepat dan konsisten, serta meninjau dan menentukan nilai akhir        |
| Guru dan pengajar jenjang pendidikan lain | Mengurangi beban koreksi esai serta menyusun soal lebih efisien                                                                         |
| Lembaga kursus dan pelatihan              | Menyediakan asesmen esai yang seragam bagi banyak peserta                                                                               |
| Mahasiswa dan peserta didik               | Mengerjakan tugas melalui akun KeyQuiz di dalam kelas, memperoleh penilaian yang adil, dan memantau nilai serta performa pada dashboard |

### 3.2.2 Potensi Pasar

Soal esai digunakan pada berbagai jenjang dan jenis asesmen, mulai dari perguruan tinggi, sekolah, hingga lembaga pelatihan, sehingga kebutuhan akan penilaian yang cepat dan konsisten bersifat luas. Sebagai aplikasi web, KeyQuiz dapat diakses oleh banyak institusi tanpa instalasi khusus. Ke depan, pengembangan dapat diarahkan pada penyediaan layanan bagi institusi pendidikan dan lembaga pelatihan, serta integrasi dengan sistem manajemen pembelajaran (Learning Management System).

## **3.3 Perancangan Project**

### 3.3.1 Arsitektur Sistem

KeyQuiz menggunakan arsitektur klien–server dengan pemisahan antara antarmuka, layanan backend, penyimpanan data, dan layanan AI, seperti ditunjukkan pada Tabel 3.2.

Tabel 3.2 Komponen Arsitektur Sistem

| **Komponen**      | **Peran**                                                                                                                                                    |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Frontend          | Antarmuka pengguna untuk login, pengelolaan kelas dan soal, halaman pengerjaan tugas, input atau pemindaian jawaban, dan dashboard (Vue.js dan Tailwind CSS) |
| Backend           | Layanan REST API yang mengatur logika penilaian dan komunikasi antarkomponen (FastAPI)                                                                       |
| Basis data        | Penyimpanan data pengguna, kelas, soal, jawaban, nilai, dan foto profil (Supabase)                                                                           |
| Basis data vektor | Penyimpanan embedding kunci jawaban dan jawaban untuk pencarian kemiripan makna (ChromaDB)                                                                   |
| Layanan AI        | Model bahasa untuk pembuatan tugas dan pendukung analisis jawaban (Qwen)                                                                                     |

### 3.3.2 Perancangan Basis Data

Basis data dirancang untuk mendukung fitur utama sistem. Entitas data dirangkum pada Tabel 3.3 dan relasi antar entitas ditunjukkan pada Gambar 3.2.

Tabel 3.3 Entitas Data pada Basis Data KeyQuiz

| **Entitas**         | **Fungsi**                                                                                                               |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| PROFILES            | Menyimpan akun pengguna, peran (dosen atau mahasiswa), NIM atau NIP, dan foto profil; autentikasi dikelola Supabase Auth |
| KELAS               | Menyimpan kelas yang dibuat dosen beserta kode kelas                                                                     |
| ANGGOTA_KELAS       | Menghubungkan kelas dengan mahasiswa yang bergabung                                                                      |
| TUGAS               | Menyimpan tugas yang dikirim dosen ke kelas beserta tenggat dan status                                                   |
| SOAL                | Menyimpan soal (pilihan ganda atau esai), urutan, dan bobot nilai                                                        |
| OPSI_JAWABAN        | Menyimpan pilihan jawaban soal pilihan ganda beserta penanda jawaban benar                                               |
| KUNCI_JAWABAN_ESSAY | Menyimpan kunci jawaban dan rubrik penilaian soal esai                                                                   |
| JAWABAN_MAHASISWA   | Menyimpan pengumpulan tugas oleh mahasiswa (dikerjakan di sistem atau hasil pindai), status, dan nilai total             |
| DETAIL_JAWABAN      | Menyimpan jawaban per soal, skor kemiripan, nilai dari AI, nilai akhir dari dosen, dan penanda revisi                    |

Gambar 3.2 Entity Relationship Diagram (ERD) KeyQuiz

Pada basis data Supabase, nilai dari AI (nilai_ai) dan nilai akhir yang ditetapkan dosen (nilai_final) disimpan terpisah pada entitas DETAIL_JAWABAN, sehingga keputusan dosen tetap tercatat dan dapat dibandingkan dengan nilai dari sistem. Embedding kunci jawaban dan jawaban mahasiswa tidak disimpan pada tabel tersebut, melainkan pada ChromaDB. Setiap dokumen di ChromaDB memakai id yang sama dengan baris pada Supabase, yaitu id KUNCI_JAWABAN_ESSAY untuk kunci jawaban dan id DETAIL_JAWABAN untuk jawaban mahasiswa, sehingga data pada kedua basis data saling terhubung.

### 3.3.3 Perancangan Antarmuka

Perancangan antarmuka dilakukan menggunakan Figma sebelum implementasi. Halaman utama yang dirancang meliputi halaman login dan registrasi, halaman kelas, pembuatan dan pengelolaan tugas, halaman pengerjaan tugas oleh mahasiswa, pemindaian jawaban, tinjauan dan koreksi nilai oleh dosen, dashboard nilai dan performa, serta profil pengguna.

Sisipkan tangkapan layar desain Figma di bagian ini.

## **3.4 Teknologi yang Digunakan**

Tabel 3.4 Teknologi yang Digunakan

| **Lapisan**       | **Teknologi**                               | **Fungsi**                                               |
| ----------------- | ------------------------------------------- | -------------------------------------------------------- |
| Frontend          | Vue.js, Tailwind CSS                        | Antarmuka pengguna                                       |
| Backend           | FastAPI, REST API                           | Logika dan layanan sistem                                |
| Basis data        | Supabase (PostgreSQL)                       | Penyimpanan data utama                                   |
| Basis data vektor | ChromaDB                                    | Pencarian kemiripan makna                                |
| Kecerdasan buatan | Model bahasa Qwen, text embedding           | Pembuatan tugas, analisis jawaban, dan analisis semantik |
| Autentikasi       | Supabase Auth, Google OAuth                 | Login dan keamanan akun                                  |
| Desain            | Figma                                       | Perancangan antarmuka                                    |
| Kolaborasi        | Git dan GitHub                              | Pengelolaan kode sumber                                  |
| Deployment        | Vercel (frontend), Render/Railway (backend) | Penyediaan aplikasi secara daring                        |

## **3.5 Prototype dan Implementasi**

### 3.5.1 Implementasi Penilaian Esai

Proses penilaian dimulai ketika dosen menyimpan kunci jawaban. Kunci jawaban diubah menjadi embedding, yaitu representasi numerik yang menangkap makna teks, lalu disimpan di ChromaDB. Representasi semacam ini umumnya dihasilkan oleh model berbasis arsitektur Transformer. Ketika jawaban mahasiswa masuk, jawaban tersebut juga diubah menjadi embedding dan dibandingkan dengan embedding kunci jawaban menggunakan ukuran kemiripan. Semakin dekat makna kedua teks, semakin tinggi skor yang dihasilkan. Untuk jawaban yang skornya berada pada rentang menengah, yaitu belum jelas sesuai atau tidak sesuai dengan kunci jawaban, model bahasa Qwen menganalisis jawaban tersebut dan meluruskannya terhadap kunci jawaban, sehingga jawaban yang bermakna sama tetapi berbeda susunan katanya tetap memperoleh nilai yang sesuai. Hasil analisis ini digunakan untuk menyesuaikan nilai dan tidak ditampilkan sebagai penjelasan kepada mahasiswa. Skor dan hasil analisis tersebut dikonversi menjadi nilai dari AI (nilai_ai) yang dapat ditinjau dosen, sedangkan nilai akhir (nilai_final) ditetapkan oleh dosen dan disimpan terpisah. Penilaian ini berlaku baik untuk jawaban yang dikerjakan langsung oleh mahasiswa pada halaman pengerjaan maupun untuk jawaban hasil pemindaian, dan dosen dapat meninjau serta mengubah nilai sebelum ditetapkan sebagai nilai akhir.

### 3.5.2 Implementasi Fitur Lainnya

- Pembuatan tugas otomatis: model bahasa Qwen membantu menghasilkan tugas berupa soal pilihan ganda atau esai beserta kunci jawabannya berdasarkan masukan dosen, sehingga tugas siap dikirim ke kelas.
- Pengerjaan tugas: mahasiswa mengerjakan tugas yang dikirim dosen melalui akun KeyQuiz pada halaman pengerjaan di dalam kelas.
- Scan Jawaban (fitur pendukung): untuk tugas yang dikerjakan di kertas, dosen memindai lembar jawaban, baik pilihan ganda maupun esai; soal dan jawaban tampil pada antarmuka sehingga dosen dapat mengoreksi atau mengubahnya, lalu hasilnya dikirim ke kelas sebagai tugas yang telah selesai dan nilai tampil pada dashboard mahasiswa.
- Dashboard: menyajikan nilai dan performa mahasiswa dari data yang tersimpan di Supabase.
- Profil pengguna: pengguna dapat mengelola profil dan mengunggah foto profil.

### 3.5.3 Deployment

Frontend aplikasi dijalankan pada Vercel, sedangkan backend FastAPI dijalankan pada Render atau Railway. Basis data dan autentikasi menggunakan Supabase, dengan opsi login melalui Google OAuth.

Sisipkan tangkapan layar prototype di bagian ini.

# **BAB IV

HASIL DAN PEMBAHASAN**

## **4.1 Hasil Project**

Hasil pengembangan project ini berupa aplikasi web KeyQuiz yang mencakup fitur penilaian esai otomatis berbasis kemiripan makna (fitur unggulan), pembuatan tugas otomatis dengan AI, pengerjaan tugas oleh mahasiswa di dalam kelas, pemindaian jawaban kertas (fitur pendukung), serta dashboard nilai dan performa.

Bagian ini menunggu tangkapan layar hasil aplikasi (halaman login, dashboard, input jawaban, hasil penilaian) dan tautan demo atau repositori.

## **4.2 Fitur dan Fungsionalitas**

Fitur dan fungsionalitas KeyQuiz dirangkum pada Tabel 4.1.

Tabel 4.1 Fitur dan Fungsionalitas KeyQuiz

| **No** | **Fitur**                                | **Deskripsi**                                                                                                                                                                                                                      |
| ------ | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1      | Registrasi dan login                     | Pengguna dapat mendaftar dan masuk menggunakan akun atau Google OAuth melalui Supabase Auth                                                                                                                                        |
| 2      | Pengelolaan kelas dan soal               | Dosen membuat kelas serta membuat, menyimpan, dan mengelola soal beserta kunci jawaban atau rubrik                                                                                                                                 |
| 3      | Penilaian esai otomatis (fitur unggulan) | Sistem membandingkan jawaban dengan kunci jawaban berdasarkan kemiripan makna dan menghasilkan skor yang dapat ditinjau dan diubah dosen, dengan bantuan model bahasa untuk jawaban yang kemiripannya berada pada rentang menengah |
| 4      | Pembuatan tugas otomatis dengan AI       | Model bahasa membuat tugas (pilihan ganda atau esai) beserta kunci jawaban yang siap dikirim dosen ke kelas                                                                                                                        |
| 5      | Pengerjaan tugas oleh mahasiswa          | Mahasiswa mengerjakan tugas melalui akun KeyQuiz pada halaman pengerjaan di dalam kelas                                                                                                                                            |
| 6      | Scan Jawaban (fitur pendukung)           | Dosen memindai jawaban dari kertas; soal dan jawaban tampil pada antarmuka dan dapat dikoreksi dosen, lalu hasilnya dikirim ke kelas sebagai tugas yang telah selesai                                                              |
| 7      | Dashboard nilai dan performa             | Menampilkan nilai dan perkembangan performa mahasiswa                                                                                                                                                                              |
| 8      | Profil pengguna                          | Pengguna dapat mengelola profil dan mengunggah foto profil                                                                                                                                                                         |

## **4.3 Pengujian**

Bagian ini menunggu data pengujian: hasil uji fungsional (black box) dan perbandingan nilai sistem dengan nilai dosen, beserta jumlah dan jenis sampel jawaban yang diuji.

# **BAB V

PENUTUP**

## **5.1 Kesimpulan**

Berdasarkan pengembangan yang telah dilakukan, dapat disimpulkan bahwa:

1. Penilaian esai secara manual rentan terhadap subjektivitas dan kurang efisien, sehingga dibutuhkan sistem yang membantu proses penilaian secara lebih konsisten.
2. KeyQuiz telah dirancang dan dikembangkan sebagai sistem penilaian esai berbasis Artificial Intelligence yang membandingkan jawaban mahasiswa dengan kunci jawaban berdasarkan kemiripan makna, yang menjadi fitur unggulan sistem.
3. Fitur pembuatan tugas otomatis dengan AI, pengerjaan tugas oleh mahasiswa di dalam kelas, pemindaian jawaban kertas sebagai fitur pendukung, dan dashboard performa melengkapi sistem sehingga mendukung proses evaluasi secara menyeluruh.
4. Sistem diposisikan sebagai alat bantu; nilai dari AI dapat ditinjau dan diubah oleh dosen sehingga keputusan akhir penilaian tetap berada pada dosen.

Kesimpulan tentang tingkat akurasi dan efektivitas sistem akan ditambahkan setelah hasil pengujian tersedia.

## **5.2 Saran**

Untuk pengembangan selanjutnya, beberapa saran yang dapat dipertimbangkan adalah:

1. Melakukan pengujian dengan data jawaban yang lebih banyak dan beragam untuk mengevaluasi akurasi sistem.
2. Mengembangkan penilaian berbasis rubrik multi-kriteria beserta penjelasan nilai untuk setiap kriteria.
3. Menambahkan dukungan integrasi dengan sistem manajemen pembelajaran.
4. Meningkatkan akurasi pengenalan tulisan tangan pada fitur pemindaian jawaban.

# **DAFTAR PUSTAKA**

Page, E. B. (1966). The imminence of grading essays by computer. _Phi Delta Kappan_, 47(5), 238–243.

Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. _Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP)_.

Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). Attention is all you need. _Advances in Neural Information Processing Systems 30 (NeurIPS 2017)_.