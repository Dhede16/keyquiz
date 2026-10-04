<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import { classes, getClassesForTeacher, saveScannedSubmission } from '@/composables/useClasses.js'
import DashboardLayout from '@/layouts/DashboardLayout.vue'
import StudentAvatar from '@/components/icons/StudentAvatar.vue'
import scanBannerImg from '@/assets/images/BennerscanSoal.png'
import { scanAnswerSheet } from '@/services/api.js'

const router = useRouter()
const { user } = useAuth()

// State: 'upload' | 'scanning' | 'result'
const currentStep = ref('upload')

const fileInput = ref(null)
const selectedFiles = ref([])
const isSelectionModalOpen = ref(false)
const selectionStep = ref('class')
const classSearch = ref('')
const studentSearch = ref('')
const classFilter = ref('all')
const showClassFilter = ref(false)
const showStudentFilter = ref(false)
const showOnlySelectedStudents = ref(false)
const selectedClassId = ref('')
const selectedStudentIds = ref([])

const teacherClasses = computed(() =>
  getClassesForTeacher(user.value?.email, user.value?.id, user.value?.name),
)

const filteredClasses = computed(() => {
  const search = classSearch.value.trim().toLocaleLowerCase()
  return teacherClasses.value.filter((classItem) => {
    const matchesSearch =
      !search ||
      [classItem.title, classItem.major, classItem.lecturer]
        .filter(Boolean)
        .some((value) => value.toLocaleLowerCase().includes(search))
    const matchesFilter = classFilter.value === 'all' || classItem.tasks?.length > 0
    return matchesSearch && matchesFilter
  })
})

const selectedClass = computed(
  () => classes.value.find((classItem) => String(classItem.id) === selectedClassId.value) || null,
)

const availableStudents = computed(() => {
  const members = selectedClass.value?.members || []
  if (members.length > 0) return members

  const submissions = (selectedClass.value?.tasks || []).flatMap((task) => task.submissions || [])
  const uniqueStudents = new Map()
  submissions.forEach((submission) => {
    const email = submission.email?.trim().toLowerCase()
    if (email && submission.studentId && !uniqueStudents.has(email)) {
      uniqueStudents.set(email, submission)
    }
  })
  return [...uniqueStudents.values()]
})
const selectedStudent = computed(() =>
  availableStudents.value.find((student) => getStudentId(student) === selectedStudentIds.value[0]),
)

const filteredStudents = computed(() => {
  const search = studentSearch.value.trim().toLocaleLowerCase()
  return availableStudents.value.filter((student) => {
    const matchesSearch =
      !search ||
      [student.name, student.email]
        .filter(Boolean)
        .some((value) => value.toLocaleLowerCase().includes(search))
    const matchesFilter =
      !showOnlySelectedStudents.value || selectedStudentIds.value.includes(getStudentId(student))
    return matchesSearch && matchesFilter
  })
})

// Scanning animation state
const scanProgress = ref(0)
const scanStatusText = ref('Menganalisis dokumen...')
const scanError = ref('')
const submissionError = ref('')
const isSubmitting = ref(false)
const savedTaskId = ref('')
let scanInterval = null

// Modal simpan
const isSavedModalOpen = ref(false)

function openClassSelection() {
  if (!canSubmitScan.value) return

  selectionStep.value = 'class'
  classSearch.value = ''
  studentSearch.value = ''
  classFilter.value = 'all'
  showOnlySelectedStudents.value = false
  showClassFilter.value = false
  showStudentFilter.value = false
  selectedClassId.value = ''
  selectedStudentIds.value = []
  submissionError.value = ''
  isSelectionModalOpen.value = true
}

function closeSelectionModal() {
  isSelectionModalOpen.value = false
}

function continueToStudentSelection() {
  if (!selectedClassId.value) return
  selectionStep.value = 'student'
  studentSearch.value = ''
  showOnlySelectedStudents.value = false
}

function togglePickerFilter() {
  if (selectionStep.value === 'class') {
    showClassFilter.value = !showClassFilter.value
    return
  }

  showStudentFilter.value = !showStudentFilter.value
}

function setClassFilter(filter) {
  classFilter.value = filter
  showClassFilter.value = false
}

function setStudentFilter(onlySelected) {
  showOnlySelectedStudents.value = onlySelected
  showStudentFilter.value = false
}

function getStudentId(student) {
  return student.studentId ?? student.id ?? student.email
}

function toggleStudentSelection(student) {
  const studentId = getStudentId(student)
  selectedStudentIds.value =
    selectedStudentIds.value[0] === studentId ? [] : [studentId]
}

const scannedQuestions = ref([])

function triggerFileInput() {
  fileInput.value?.click()
}

function onFileChange(event) {
  const files = Array.from(event.target.files || [])
  if (files.length > 0) {
    const file = files[0]
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      selectedFiles.value = []
      scanError.value = 'Format yang didukung hanya JPG, PNG, atau WEBP.'
    } else {
      selectedFiles.value = [file]
      scanError.value = ''
    }
  }
  event.target.value = ''
}

function removeFile(index) {
  selectedFiles.value.splice(index, 1)
}

function clearAllFiles() {
  selectedFiles.value = []
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

// Mulai proses scanning dengan animasi loading dan panggilan backend Vision AI
async function startScanning() {
  if (selectedFiles.value.length === 0 || scanInterval) return
  currentStep.value = 'scanning'
  scanError.value = ''
  scannedQuestions.value = []
  scanProgress.value = 0
  scanStatusText.value = 'Membaca dokumen dan foto soal...'

  // Jalankan animasi progress
  let progress = 0
  scanInterval = setInterval(() => {
    if (progress < 90) {
      progress += 5
      scanProgress.value = progress
      if (progress < 35) {
        scanStatusText.value = 'Membaca teks dari lembar foto...'
      } else if (progress < 75) {
        scanStatusText.value = 'AI mengekstrak soal, opsi, dan jawaban bertanda...'
      } else {
        scanStatusText.value = 'Menyiapkan hasil koreksi soal...'
      }
    }
  }, 100)

  try {
    const scanRes = await scanAnswerSheet({
      file: selectedFiles.value[0],
      jenis: 'pilihan_ganda',
    })
    const rows = scanRes?.jawaban_terbaca || []
    if (rows.some((item) => !item.pertanyaan || !Array.isArray(item.opsi) || item.opsi.length < 2)) {
      throw new Error(
        'Backend scan yang sedang berjalan masih memakai format lama dan belum mengirim teks soal serta opsi. Restart backend dari folder backend, lalu coba scan lagi.',
      )
    }
    scannedQuestions.value = rows.map((item, idx) => ({
      id: idx + 1,
      nomor: item.nomor || idx + 1,
      soal: item.pertanyaan || `Soal Nomor ${item.nomor || idx + 1}`,
      options: (item.opsi || []).map((option) => ({
        value: String(option.huruf).toUpperCase(),
        label: `${String(option.huruf).toUpperCase()}. ${option.teks}`,
      })),
      selectedOption: item.pilihan ? item.pilihan.toUpperCase() : '',
      answerKey: '',
      points: 10,
      score: 0,
      isCertain: item.yakin !== false,
    }))
    if (scannedQuestions.value.length === 0) {
      throw new Error('AI tidak menemukan soal pada foto. Unggah foto soal pilihan ganda yang lebih jelas.')
    }
    currentStep.value = 'result'
  } catch (err) {
    scanError.value = err.message || 'Gagal memindai foto. Silakan coba lagi.'
    currentStep.value = 'upload'
  } finally {
    clearInterval(scanInterval)
    scanInterval = null
    scanProgress.value = 100
  }
}

onUnmounted(() => {
  if (scanInterval) clearInterval(scanInterval)
})

function updateQuestionScore(question) {
  const isCorrect = question.answerKey && question.answerKey === question.selectedOption
  question.score = isCorrect ? Number(question.points) || 0 : 0
}

function updateQuestionPoints(question) {
  const points = Number(question.points)
  question.points = Number.isFinite(points) ? Math.max(points, 0) : 0
  question.score = Math.min(Number(question.score) || 0, question.points)
}

const totalScore = computed(() =>
  scannedQuestions.value.reduce((sum, question) => sum + (Number(question.score) || 0), 0),
)
const maxScore = computed(() =>
  scannedQuestions.value.reduce((sum, question) => sum + (Number(question.points) || 0), 0),
)
const canSubmitScan = computed(
  () =>
    scannedQuestions.value.length > 0 &&
    scannedQuestions.value.every(
      (question) =>
        question.soal.trim() &&
        question.options.length >= 2 &&
        new Set(question.options.map((option) => option.value)).size === question.options.length &&
        question.answerKey &&
        Number.isFinite(Number(question.score)) &&
        Number(question.score) >= 0 &&
        Number(question.score) <= Number(question.points),
    ),
)

async function submitScannedResult() {
  if (isSubmitting.value || !selectedClassId.value || !selectedStudentIds.value.length) return
  isSubmitting.value = true
  submissionError.value = ''

  try {
    const task = await saveScannedSubmission(
      selectedClassId.value,
      selectedStudentIds.value[0],
      scannedQuestions.value.map((question) => ({
        title: question.soal,
        options: question.options,
        selectedOption: question.selectedOption,
        answerKey: question.answerKey,
        points: Number(question.points),
        score: Number(question.score),
        isCertain: question.isCertain,
      })),
      selectedFiles.value[0].name,
    )
    savedTaskId.value = task.id
    isSelectionModalOpen.value = false
    isSavedModalOpen.value = true
  } catch (err) {
    submissionError.value = err.message || 'Gagal mengirim hasil scan. Silakan coba lagi.'
  } finally {
    isSubmitting.value = false
  }
}

// Reset dan scan file baru
function resetScan() {
  currentStep.value = 'upload'
  isSavedModalOpen.value = false
  scanError.value = ''
  scannedQuestions.value = []
  clearAllFiles()
}

// Teks dinamis kartu bawah saat tahap upload
const cardTitle = computed(() => {
  return selectedFiles.value.length > 0 ? 'Foto siap dipindai' : 'Koreksi Jawaban Menggunakan AI'
})

const cardSubtitle = computed(() => {
  return 'Unggah satu foto lembar soal pilihan ganda yang sudah dijawab (JPG, PNG, atau WEBP).'
})

const buttonText = computed(() => {
  return selectedFiles.value.length > 0 ? 'Mulai Scan AI' : 'Pilih Foto Lembar Jawaban'
})
</script>

<template>
  <DashboardLayout>
    <!-- ========================================== -->
    <!-- TAHAP 1: UPLOAD DOKUMEN                    -->
    <!-- ========================================== -->
    <div v-if="currentStep === 'upload'" class="space-y-4 sm:space-y-[22px]">
      <!-- Satu lembar scan dikaitkan dengan satu mahasiswa -->
      <input
        ref="fileInput"
        type="file"
        class="hidden"
        accept="image/jpeg,image/png,image/webp"
        @change="onFileChange"
      />

      <!-- Banner halaman scan soal -->
      <section
        class="overflow-hidden rounded-[1.5rem] border-4 border-white bg-white shadow-sm sm:rounded-[2rem]"
      >
        <img
          :src="scanBannerImg"
          alt="Koreksi jawaban lebih mudah menggunakan AI"
          class="block aspect-[4.7/1] w-full object-cover"
        />
      </section>

      <!-- Bagian Bawah: Koreksi Jawaban Menggunakan AI -->
      <section
        class="flex flex-col items-center justify-center rounded-[1.5rem] bg-white px-5 py-12 text-center transition-all duration-300 sm:rounded-[2rem] sm:px-10 sm:py-16 lg:rounded-[2.5rem] lg:py-20"
      >
        <h2
          class="text-xl font-bold text-[#222222] transition-all duration-300 sm:text-3xl lg:text-4xl"
        >
          {{ cardTitle }}
        </h2>

        <p
          class="mt-2 text-sm text-[#555555] transition-all duration-300 sm:mt-3 sm:text-base lg:text-lg"
        >
          {{ cardSubtitle }}
        </p>
        <p v-if="scanError" role="alert" class="mt-3 text-sm font-medium text-red-600">
          {{ scanError }}
        </p>

        <!-- Informasi file-file yang terpilih (Multi-upload Support) -->
        <div
          v-if="selectedFiles.length > 0"
          class="mt-6 flex flex-wrap items-center justify-center gap-2.5 max-w-2xl animate-fade-in"
        >
          <div
            v-for="(f, fIdx) in selectedFiles"
            :key="fIdx"
            class="flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-xs sm:text-sm text-[#222222] shadow-xs"
          >
            <!-- Ikon Foto/Dokumen -->
            <svg
              class="size-4 text-[#2864E8] shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <span class="max-w-[150px] sm:max-w-[200px] truncate font-medium">
              {{ f.name }}
            </span>
            <span class="text-[11px] text-[#777777]"> ({{ formatFileSize(f.size) }}) </span>
            <!-- Tombol Hapus Satuan -->
            <button
              type="button"
              class="ml-1 cursor-pointer text-slate-400 transition hover:text-red-500"
              title="Hapus foto ini"
              @click="removeFile(fIdx)"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- Tombol Aksi -->
        <div class="mt-8 flex flex-wrap items-center justify-center gap-3 sm:mt-10">
          <button
            type="button"
            class="cursor-pointer rounded-xl bg-[#2864E8] px-8 py-3.5 text-base font-semibold text-white shadow-md transition duration-200 hover:bg-[#1f52c4] hover:shadow-lg active:scale-[0.98] sm:px-10 sm:py-4 sm:text-lg"
            @click="selectedFiles.length > 0 ? startScanning() : triggerFileInput()"
          >
            {{ buttonText }}
          </button>

          <!-- Ganti foto sebelum memulai scan -->
          <button
            v-if="selectedFiles.length > 0"
            type="button"
            class="cursor-pointer rounded-xl border border-slate-300 bg-white px-5 py-3.5 text-sm font-semibold text-[#555555] transition hover:bg-slate-50 sm:text-base sm:py-4"
            @click="triggerFileInput"
          >
            Ganti Foto
          </button>
        </div>
      </section>
    </div>

    <!-- ========================================== -->
    <!-- TAHAP 2: ANIMASI SCANNING & LOADING AI     -->
    <!-- ========================================== -->
    <div
      v-else-if="currentStep === 'scanning'"
      class="flex min-h-[500px] flex-col items-center justify-center rounded-[1.5rem] bg-white p-8 text-center shadow-lg transition-all duration-300 sm:rounded-[2rem] sm:p-14 lg:h-[calc(100vh-140px)]"
    >
      <div class="relative flex flex-col items-center max-w-md w-full">
        <!-- Visual scanner animasi -->
        <div class="relative mb-8 flex size-28 items-center justify-center sm:size-36">
          <div class="absolute inset-0 rounded-3xl bg-[#2864E8]/15 blur-xl animate-pulse"></div>

          <div
            class="relative flex size-24 items-center justify-center rounded-2xl border-2 border-[#2864E8]/30 bg-blue-50/50 shadow-inner sm:size-28 overflow-hidden"
          >
            <svg
              class="size-12 text-[#2864E8] sm:size-14"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.75"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <div
              class="scanner-beam pointer-events-none absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-[#2864E8] to-transparent shadow-[0_0_12px_#2864E8]"
            ></div>
          </div>

          <div
            class="absolute inset-0 rounded-3xl border border-[#2864E8]/40 animate-ping opacity-40"
          ></div>
        </div>

        <h2 class="text-xl font-bold text-[#222222] sm:text-2xl">Memindai Soal Kuis</h2>
        <p class="mt-2 text-sm text-[#777777] sm:text-base">
          {{ scanStatusText }}
        </p>

        <!-- Progress Bar & Persentase -->
        <div class="mt-7 w-full max-w-xs">
          <div class="flex items-center justify-between text-xs font-semibold text-[#2864E8] mb-2">
            <span>Proses AI</span>
            <span>{{ scanProgress }}%</span>
          </div>
          <div class="h-2 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              class="h-full rounded-full bg-gradient-to-r from-[#2864E8] to-[#558cf7] transition-all duration-100 ease-out shadow-[0_0_8px_#2864E8]"
              :style="{ width: `${scanProgress}%` }"
            ></div>
          </div>
        </div>

        <!-- Nama Dokumen / Jumlah Foto yang diproses -->
        <div
          class="mt-6 flex items-center gap-2 rounded-full bg-slate-100 px-4 py-1.5 text-xs text-[#555555]"
        >
          <span class="size-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span class="truncate max-w-[240px]">
            {{
              selectedFiles.length > 1
                ? `${selectedFiles.length} Foto Soal Diproses`
                : selectedFiles[0]?.name || 'Dokumen Kuis'
            }}
          </span>
        </div>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- TAHAP 3: HASIL SCAN SOAL (PERSIS SESUAI FOTO MOCKUP PENGGUNA)   -->
    <!-- ============================================================== -->
    <div v-else-if="currentStep === 'result'" class="space-y-4 sm:space-y-[22px]">
      <!-- Banner hasil koreksi soal -->
      <section
        class="overflow-hidden rounded-[1.5rem] border-4 border-white bg-white shadow-sm sm:rounded-[2rem]"
      >
        <img
          :src="scanBannerImg"
          alt="Koreksi jawaban lebih mudah menggunakan AI"
          class="block aspect-[4.7/1] w-full object-cover"
        />
      </section>

      <section class="rounded-2xl bg-white p-4 shadow-sm sm:p-6">
        <h2 class="text-lg font-bold text-[#222222]">Periksa hasil scan dan nilai</h2>
        <p class="mt-1 text-sm text-[#666666]">
          Periksa teks soal dan opsi, koreksi jawaban yang terbaca, tentukan kunci jawaban, lalu
          sesuaikan nilai jika diperlukan.
        </p>
        <p class="mt-3 text-sm font-semibold text-[#2864E8]">
          Nilai sementara: {{ totalScore }} / {{ maxScore }} poin
        </p>
      </section>

      <div class="space-y-4 sm:space-y-[18px]">
        <div
          v-for="item in scannedQuestions"
          :key="item.id"
          class="rounded-2xl bg-white p-4 shadow-sm transition duration-200 hover:shadow-md sm:p-6"
        >
          <div class="min-w-0">
            <h2 class="text-base font-semibold text-[#222222] sm:text-lg">
              Soal {{ item.nomor }}. {{ item.soal }}
            </h2>
            <div class="my-2 h-px w-full bg-[#d9d9d9]"></div>

            <div v-if="item.options.length" class="space-y-1">
              <div
                v-for="option in item.options"
                :key="option.value"
                class="flex items-start gap-2.5 text-sm text-[#222222] sm:text-base"
              >
                <span
                  class="mt-1 flex size-4 shrink-0 items-center justify-center rounded-full border"
                  :class="item.selectedOption === option.value ? 'border-[#2864E8]' : 'border-[#999999]'"
                ><span v-if="item.selectedOption === option.value" class="size-2 rounded-full bg-[#2864E8]" /></span>
                {{ option.label }}
              </div>
            </div>
            <p v-else class="text-sm text-amber-700">
              Opsi jawaban tidak terbaca. Foto ini belum dapat dikirim untuk penilaian pilihan ganda.
            </p>

            <p v-if="!item.isCertain" class="mt-2 text-sm font-medium text-amber-700">
              AI ragu membaca tanda jawaban. Mohon periksa dan koreksi jawaban yang terbaca.
            </p>

            <div class="mt-4 grid gap-3 sm:grid-cols-2">
              <label class="space-y-1 text-sm font-medium text-[#444444]">
                Jawaban yang ditandai siswa
                <select
                  v-model="item.selectedOption"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2"
                  @change="updateQuestionScore(item)"
                >
                  <option value="">Tidak terdeteksi / kosong</option>
                  <option v-for="option in item.options" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </label>
              <label class="space-y-1 text-sm font-medium text-[#444444]">
                Kunci jawaban dosen
                <select
                  v-model="item.answerKey"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2"
                  @change="updateQuestionScore(item)"
                >
                  <option value="">Pilih kunci jawaban</option>
                  <option v-for="option in item.options" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </label>
              <label class="space-y-1 text-sm font-medium text-[#444444]">
                Bobot soal
                <input
                  v-model.number="item.points"
                  type="number"
                  min="0"
                  step="0.5"
                  class="w-full rounded-lg border border-slate-300 px-3 py-2"
                  @input="updateQuestionPoints(item)"
                />
              </label>
              <label class="space-y-1 text-sm font-medium text-[#444444]">
                Nilai mahasiswa
                <input
                  v-model.number="item.score"
                  type="number"
                  min="0"
                  :max="item.points"
                  step="0.5"
                  class="w-full rounded-lg border border-slate-300 px-3 py-2"
                />
              </label>
            </div>
          </div>
        </div>
      </div>

      <div class="flex flex-col items-end gap-2 pt-4 sm:pt-6">
        <p v-if="!canSubmitScan" class="text-right text-sm text-amber-700">
          Lengkapi opsi dan kunci jawaban setiap soal. Nilai harus berada di antara 0 dan bobot soal.
        </p>
        <button
          type="button"
          class="cursor-pointer rounded-xl border border-white/80 bg-transparent px-10 py-3 text-base font-semibold text-white transition duration-200 hover:bg-white/10 active:scale-95 sm:px-12 sm:py-3.5 sm:text-lg"
          :disabled="!canSubmitScan"
          :class="{ 'cursor-not-allowed opacity-50': !canSubmitScan }"
          @click="openClassSelection"
        >
          Pilih Kelas & Mahasiswa
        </button>
      </div>
    </div>

    <Teleport to="body">
      <Transition name="picker-modal">
        <div
          v-if="isSelectionModalOpen"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-3 backdrop-blur-sm sm:p-6"
          @click.self="closeSelectionModal"
        >
          <section
            class="flex max-h-[calc(100dvh-24px)] w-full max-w-[680px] flex-col overflow-hidden rounded-2xl bg-white shadow-2xl sm:max-h-[calc(100dvh-48px)]"
            role="dialog"
            aria-modal="true"
            :aria-labelledby="`picker-title-${selectionStep}`"
          >
            <header
              class="relative flex min-h-[76px] shrink-0 items-center justify-center bg-[linear-gradient(105deg,#2864E8_0%,#173C87_100%)] px-14 py-4 text-center text-white sm:min-h-[100px]"
            >
              <button
                v-if="selectionStep === 'student'"
                type="button"
                class="absolute left-4 flex size-9 items-center justify-center rounded-full text-white/90 transition hover:bg-white/10 hover:text-white sm:left-6"
                aria-label="Kembali memilih kelas"
                @click="selectionStep = 'class'"
              >
                <svg class="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </button>
              <h2 :id="`picker-title-${selectionStep}`" class="text-xl font-bold sm:text-3xl">
                {{ selectionStep === 'class' ? 'Pilih Kelas' : 'Pilih Mahasiswa' }}
              </h2>
              <button
                type="button"
                class="absolute right-4 flex size-9 items-center justify-center rounded-full text-white/90 transition hover:bg-white/10 hover:text-white sm:right-6"
                aria-label="Tutup pemilihan"
                @click="closeSelectionModal"
              >
                <svg class="size-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.75"
                    d="M6 6l12 12M18 6L6 18"
                  />
                </svg>
              </button>
            </header>

            <div class="flex min-h-0 flex-1 flex-col px-5 pb-5 pt-4 sm:px-7 sm:pb-7 sm:pt-5">
              <p v-if="selectionStep === 'student'" class="mb-2 text-sm text-[#666666]">
                Satu lembar scan hanya dapat dikaitkan dengan satu mahasiswa.
              </p>
              <div class="relative flex shrink-0 items-center gap-3">
                <label class="relative min-w-0 flex-1">
                  <span class="sr-only"
                    >Cari {{ selectionStep === 'class' ? 'kelas' : 'mahasiswa' }}</span
                  >
                  <svg
                    class="pointer-events-none absolute left-4 top-1/2 size-6 -translate-y-1/2 text-[#888888]"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <circle cx="10.8" cy="10.8" r="7.3" stroke-width="1.8" />
                    <path d="m16.2 16.2 4.2 4.2" stroke-width="1.8" stroke-linecap="round" />
                  </svg>
                  <input
                    v-if="selectionStep === 'class'"
                    v-model="classSearch"
                    type="search"
                    placeholder="Cari kelas"
                    class="h-12 w-full rounded-xl border border-[#888888] bg-white pl-12 pr-3 text-sm outline-none focus:border-[#2864E8] sm:h-[58px] sm:text-base"
                  />
                  <input
                    v-else
                    v-model="studentSearch"
                    type="search"
                    placeholder="Cari mahasiswa"
                    class="h-12 w-full rounded-xl border border-[#888888] bg-white pl-12 pr-3 text-sm outline-none focus:border-[#2864E8] sm:h-[58px] sm:text-base"
                  />
                </label>

                <div class="relative shrink-0">
                  <button
                    type="button"
                    class="flex size-12 items-center justify-center rounded-xl border border-transparent text-[#808080] transition hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-[#2864E8] sm:size-[58px]"
                    :aria-label="selectionStep === 'class' ? 'Filter kelas' : 'Filter mahasiswa'"
                    :aria-expanded="selectionStep === 'class' ? showClassFilter : showStudentFilter"
                    @click="togglePickerFilter"
                  >
                    <svg
                      class="size-7 sm:size-8"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="1.7"
                        d="M3 5h18l-7 8v5l-4 2v-7L3 5z"
                      />
                    </svg>
                  </button>

                  <div
                    v-if="selectionStep === 'class' && showClassFilter"
                    class="absolute right-0 top-full z-10 mt-1 w-44 rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg"
                  >
                    <button
                      type="button"
                      class="w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-blue-50"
                      @click="setClassFilter('all')"
                    >
                      Semua kelas
                    </button>
                    <button
                      type="button"
                      class="w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-blue-50"
                      @click="setClassFilter('has-quizzes')"
                    >
                      Kelas dengan kuis
                    </button>
                  </div>
                  <div
                    v-else-if="selectionStep === 'student' && showStudentFilter"
                    class="absolute right-0 top-full z-10 mt-1 w-48 rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg"
                  >
                    <button
                      type="button"
                      class="w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-blue-50"
                      @click="setStudentFilter(false)"
                    >
                      Semua mahasiswa
                    </button>
                    <button
                      type="button"
                      class="w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-blue-50"
                      @click="setStudentFilter(true)"
                    >
                      Mahasiswa dipilih
                    </button>
                  </div>
                </div>
              </div>

              <div class="min-h-0 flex-1 space-y-3 overflow-y-auto py-4 sm:space-y-4">
                <template v-if="selectionStep === 'class'">
                  <button
                    v-for="classItem in filteredClasses"
                    :key="classItem.id"
                    type="button"
                    class="w-full rounded-2xl border px-5 py-4 text-left shadow-[0_2px_4px_rgba(0,0,0,0.2)] transition sm:px-7 sm:py-5"
                    :class="
                      selectedClassId === String(classItem.id)
                        ? 'border-[#2864E8] ring-2 ring-[#2864E8]/20'
                        : 'border-[#888888] hover:border-[#2864E8]'
                    "
                    @click="selectedClassId = String(classItem.id)"
                  >
                    <h3
                      class="truncate border-b border-[#aaaaaa] pb-2 text-lg text-[#808080] sm:text-2xl"
                    >
                      {{ classItem.title }}
                    </h3>
                    <p class="mt-2 text-sm text-[#808080] sm:text-lg">
                      {{ classItem.major || classItem.code || 'Kelas' }}
                    </p>
                  </button>
                  <p
                    v-if="filteredClasses.length === 0"
                    class="py-8 text-center text-sm text-[#888888]"
                  >
                    Kelas tidak ditemukan.
                  </p>
                </template>

                <template v-else>
                  <button
                    v-for="student in filteredStudents"
                    :key="getStudentId(student)"
                    type="button"
                    class="flex w-full items-center gap-3 rounded-2xl border px-2 py-2 text-left shadow-[0_2px_4px_rgba(0,0,0,0.2)] transition sm:gap-4 sm:px-3"
                    :class="
                      selectedStudentIds.includes(getStudentId(student))
                        ? 'border-[#2864E8] bg-blue-50/50'
                        : 'border-[#888888] hover:border-[#2864E8]'
                    "
                    :aria-pressed="selectedStudentIds.includes(getStudentId(student))"
                    @click="toggleStudentSelection(student)"
                  >
                    <div class="size-[68px] shrink-0 overflow-hidden rounded-xl sm:size-[88px]">
                      <StudentAvatar />
                    </div>
                    <div class="min-w-0 flex-1">
                      <h3 class="truncate text-base font-semibold text-[#808080] sm:text-xl">
                        {{ student.name || student.email }}
                      </h3>
                      <p class="truncate text-sm text-[#888888] sm:text-base">
                        {{ student.email }}
                      </p>
                    </div>
                    <span
                      class="flex size-6 shrink-0 items-center justify-center rounded-full border"
                      :class="
                        selectedStudentIds.includes(getStudentId(student))
                          ? 'border-[#2864E8] bg-[#2864E8] text-white'
                          : 'border-[#aaaaaa] text-transparent'
                      "
                      aria-hidden="true"
                    >
                      <svg class="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="3"
                          d="m5 12 4 4L19 6"
                        />
                      </svg>
                    </span>
                  </button>
                  <p
                    v-if="filteredStudents.length === 0"
                    class="py-8 text-center text-sm text-[#888888]"
                  >
                    Mahasiswa tidak ditemukan.
                  </p>
                </template>
              </div>

              <p v-if="submissionError" role="alert" class="mt-3 text-sm font-medium text-red-600">
                {{ submissionError }}
              </p>
              <footer class="flex shrink-0 justify-end border-t border-slate-100 pt-4">
                <button
                  v-if="selectionStep === 'class'"
                  type="button"
                  :disabled="!selectedClassId"
                  class="min-h-12 w-full rounded-xl bg-[#2864E8] px-8 text-base font-semibold text-white transition hover:bg-[#1f50be] disabled:cursor-not-allowed disabled:opacity-50 sm:min-h-[58px] sm:w-auto sm:min-w-[200px] sm:text-lg"
                  @click="continueToStudentSelection"
                >
                  Selanjutnya
                </button>
                <button
                  v-else
                  type="button"
                  :disabled="selectedStudentIds.length === 0 || isSubmitting"
                  class="min-h-12 w-full rounded-xl bg-[#2864E8] px-8 text-base font-semibold text-white transition hover:bg-[#1f50be] disabled:cursor-not-allowed disabled:opacity-50 sm:min-h-[58px] sm:w-auto sm:min-w-[200px] sm:text-lg"
                  @click="submitScannedResult"
                >
                  {{ isSubmitting ? 'Mengirim...' : 'Kirim Hasil Scan' }}
                </button>
              </footer>
            </div>
          </section>
        </div>
      </Transition>
    </Teleport>

    <!-- ========================================== -->
    <!-- MODAL POPUP: BERHASIL DISIMPAN             -->
    <!-- ========================================== -->
    <div
      v-if="isSavedModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-xs animate-fade-in"
      @click.self="isSavedModalOpen = false"
    >
      <div
        class="w-full max-w-md rounded-3xl bg-white p-6 sm:p-8 text-center shadow-2xl animate-scale-up"
      >
        <!-- Ikon Sukses -->
        <div
          class="mx-auto flex size-16 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 sm:size-20"
        >
          <svg class="size-8 sm:size-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2.5"
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>

        <h3 class="mt-5 text-xl font-bold text-[#222222] sm:text-2xl">Hasil Scan Terkirim!</h3>

        <p class="mt-2 text-sm text-[#666666] sm:text-base">
          Hasil untuk
          <strong class="text-[#2864E8]">{{ selectedStudent?.name || selectedStudent?.email }}</strong>
          telah dikirim ke kelas <strong>{{ selectedClass?.title }}</strong>. Nilai:
          <strong class="text-[#2864E8]">{{ totalScore }} / {{ maxScore }}</strong>.
        </p>

        <!-- Tombol Aksi Modal -->
        <div class="mt-7 flex flex-col gap-2.5 sm:flex-row sm:justify-center">
          <button
            type="button"
            class="cursor-pointer rounded-xl bg-[#2864E8] px-6 py-3 text-sm font-semibold text-white shadow-md transition hover:bg-[#1f52c4] active:scale-95 sm:text-base"
            @click="router.push(`/kelas/${selectedClassId}/tugas/${savedTaskId}`)"
          >
            Lihat Hasil di Kelas
          </button>
          <button
            type="button"
            class="cursor-pointer rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-[#555555] transition hover:bg-slate-50 sm:text-base"
            @click="resetScan"
          >
            Scan Soal Baru
          </button>
        </div>
      </div>
    </div>
  </DashboardLayout>
</template>

<style scoped>
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fadeIn 0.25s ease-out forwards;
}

@keyframes scaleUp {
  from {
    opacity: 0;
    transform: scale(0.92);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-scale-up {
  animation: scaleUp 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes scanSweep {
  0% {
    top: 0%;
    opacity: 0.2;
  }
  50% {
    top: 90%;
    opacity: 1;
  }
  100% {
    top: 0%;
    opacity: 0.2;
  }
}

.scanner-beam {
  animation: scanSweep 1.8s ease-in-out infinite;
}

.picker-modal-enter-active,
.picker-modal-leave-active {
  transition: opacity 0.2s ease;
}

.picker-modal-enter-from,
.picker-modal-leave-to {
  opacity: 0;
}
</style>
