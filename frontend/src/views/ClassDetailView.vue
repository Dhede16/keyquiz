<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import DashboardLayout from '@/layouts/DashboardLayout.vue'
import { defaultStudents } from '@/data/students.js'
import {
  addTaskToClass,
  classes,
  getScannedArchiveImageUrl,
} from '@/composables/useClasses.js'
import { canStudentViewTask, canTeacherViewTask } from '@/utils/scannedTaskAccess.js'
import { getClassStatisticsStudents } from '@/utils/classStatistics.js'
import classDetailBanner from '@/assets/images/BennedetailClass.png'

const route = useRoute()
const router = useRouter()
const { user } = useAuth()

const classId = computed(() => route.params.id || 1)
const isStudent = computed(() => user.value?.role === 'student')

// Ambil data kelas atau fallback ke kelas pertama
const currentClass = computed(() => {
  return (
    classes.value.find((c) => String(c.id) === String(classId.value)) ||
    (isStudent.value ? null : classes.value[0])
  )
})

const allTasks = computed(() =>
  [...(currentClass.value?.tasks || [])].sort(
    (a, b) =>
      (Date.parse(b.createdAt || '') || 0) - (Date.parse(a.createdAt || '') || 0),
  ),
)
const tasks = computed(() =>
  allTasks.value.filter((task) =>
    isStudent.value
      ? canStudentViewTask(task, user.value?.id, user.value?.email)
      : canTeacherViewTask(task),
  ),
)
const statisticsTasks = computed(() => (isStudent.value ? tasks.value : allTasks.value))
const activeClassTab = ref(route.query.tab === 'archives' ? 'archives' : 'quizzes')
const selectedArchiveFolderId = ref(route.query.folderId || '')
const selectedArchive = ref(null)
const archiveImageUrl = ref('')
const archiveImageError = ref('')
const isLoadingArchiveImage = ref(false)
const archiveFolders = computed(() =>
  [...(currentClass.value?.archiveFolders || [])].sort(
    (a, b) => (Date.parse(b.createdAt || '') || 0) - (Date.parse(a.createdAt || '') || 0),
  ),
)
const selectedArchiveFolder = computed(
  () => archiveFolders.value.find((folder) => folder.id === selectedArchiveFolderId.value) || null,
)
const selectedStatisticStudent = ref(null)
const classStatisticsStudents = computed(() => {
  return getClassStatisticsStudents(currentClass.value?.members || [], statisticsTasks.value)
})
const currentStudentStatistics = computed(() => {
  const email = user.value?.email?.trim().toLowerCase()
  const sampleStudent = defaultStudents.find((student) => student.email.toLowerCase() === email)
  const submissions = statisticsTasks.value.map((task) =>
    task.submissions?.find((submission) => submission.email?.trim().toLowerCase() === email),
  )
  const quizScores = statisticsTasks.value.map((task, index) => {
    const submission = submissions[index]
    if (!submission) return { id: task.id, title: task.title, score: null, completed: false }

    const rawScore = submission.graded || submission.score != null ? Number(submission.score) : null
    const maxScore =
      Number(submission.maxScore) ||
      (task.questions || []).reduce((total, question) => total + (Number(question.points) || 0), 0)

    return {
      id: task.id,
      title: task.title,
      score:
        rawScore === null
          ? null
          : maxScore > 0
            ? Math.round((rawScore / maxScore) * 100)
            : rawScore,
      completed: true,
    }
  })
  const gradedScores = quizScores
    .filter((quiz) => Number.isFinite(quiz.score))
    .map((quiz) => quiz.score)

  return {
    name: user.value?.name || sampleStudent?.name || 'Mahasiswa',
    email: user.value?.email || sampleStudent?.email || '',
    average:
      gradedScores.length > 0
        ? Math.round(gradedScores.reduce((total, score) => total + score, 0) / gradedScores.length)
        : 0,
    quizScores,
  }
})
const visibleStatisticStudent = computed(() =>
  isStudent.value ? currentStudentStatistics.value : selectedStatisticStudent.value,
)
const statisticChartWidth = computed(() => `${Math.max(520, statisticsTasks.value.length * 150)}px`)

function getScoreHeight(score) {
  return `${Math.min(100, Math.max(0, Number(score) || 0))}%`
}

function formatTaskDeadline(task) {
  const rawDate = task.deadlineDate || task.dueAt?.slice(0, 10)
  if (!rawDate) {
    return task.date?.replace('September', 'Sep').replace('Oktober', 'Okt') || 'Belum ditentukan'
  }

  return new Date(`${rawDate}T12:00:00`).toLocaleDateString('id-ID', {
    weekday: 'long',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

function selectClassTab(tab) {
  activeClassTab.value = tab
  if (tab === 'quizzes') selectedStatisticStudent.value = null
  if (tab === 'archives') selectedArchiveFolderId.value = ''
}

async function openArchive(archive) {
  selectedArchive.value = archive
  archiveImageUrl.value = ''
  archiveImageError.value = ''
  isLoadingArchiveImage.value = true

  try {
    archiveImageUrl.value = await getScannedArchiveImageUrl(archive.originalFilePath)
  } catch (error) {
    archiveImageError.value = error.message || 'Foto arsip tidak dapat dibuka.'
  } finally {
    isLoadingArchiveImage.value = false
  }
}

function closeArchive() {
  selectedArchive.value = null
  archiveImageUrl.value = ''
  archiveImageError.value = ''
}

// Salin kode kelas
const classCodeCopied = ref(false)
function copyClassCode() {
  if (!currentClass.value?.code) return
  navigator.clipboard.writeText(currentClass.value.code).then(() => {
    classCodeCopied.value = true
    setTimeout(() => { classCodeCopied.value = false }, 2000)
  })
}

// Modal Pilihan Metode Pembuatan Soal (AI vs Manual)
const isChoiceModalOpen = ref(false)

// Modal Tambah Tugas Manual
const isAddTaskModalOpen = ref(false)
const newTaskTitle = ref('')
const newTaskDesc = ref('')

function handleFabClick() {
  isChoiceModalOpen.value = true
}

function handleChooseAi() {
  isChoiceModalOpen.value = false
  router.push(`/kelas/${classId.value}/buat-soal-ai`)
}

function handleChooseManual() {
  isChoiceModalOpen.value = false
  router.push(`/kelas/${classId.value}/buat-soal-manual`)
}

function openAddTaskModal() {
  newTaskTitle.value = `Tugas ${tasks.value.length + 1}`
  newTaskDesc.value = ''
  isAddTaskModalOpen.value = true
}

function closeAddTaskModal() {
  isAddTaskModalOpen.value = false
}

function handleAddTask() {
  if (!newTaskTitle.value.trim()) return

  const now = new Date()
  const options = { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }
  const formattedDate = now.toLocaleDateString('id-ID', options)

  addTaskToClass(classId.value, {
    id: Date.now(),
    title: newTaskTitle.value.trim(),
    date: formattedDate,
    description: newTaskDesc.value.trim(),
  })

  closeAddTaskModal()
}

function handleTaskClick(task) {
  router.push(`/kelas/${classId.value}/tugas/${task.id}`)
}

function getStudentSubmission(task) {
  const email = user.value?.email?.trim().toLowerCase()
  if (!email) return null

  return (
    task.submissions?.find((submission) => submission.email?.trim().toLowerCase() === email) || null
  )
}
</script>

<template>
  <DashboardLayout>
    <div class="relative space-y-4 sm:space-y-6">
      <!-- Banner Detail Kelas -->
      <section
        class="overflow-hidden rounded-[1.5rem] border-4 border-white bg-white shadow-sm sm:rounded-[2rem]"
      >
        <img
          :src="classDetailBanner"
          alt="Selamat datang di kelas KeyQuiz"
          class="block aspect-[4.7/1] w-full object-cover"
        />
      </section>

      <!-- Kode Kelas (hanya untuk dosen) -->
      <section
        v-if="!isStudent && currentClass?.code"
        class="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-blue-200 bg-blue-50 px-5 py-3.5 shadow-sm"
      >
        <div class="flex items-center gap-3">
          <svg class="size-5 shrink-0 text-[#2864E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
          <div>
            <p class="text-xs font-semibold text-slate-500">Kode Bergabung Kelas</p>
            <p class="font-mono text-lg font-bold tracking-widest text-[#2864E8]">{{ currentClass.code }}</p>
          </div>
        </div>
        <button
          id="copy-class-code-btn"
          type="button"
          class="cursor-pointer rounded-xl border border-[#2864E8] px-4 py-2 text-sm font-semibold text-[#2864E8] transition hover:bg-[#2864E8] hover:text-white active:scale-95"
          @click="copyClassCode"
        >
          {{ classCodeCopied ? '✓ Tersalin!' : 'Salin Kode' }}
        </button>
      </section>

      <div
        class="grid gap-1 rounded-xl border border-white bg-white p-1 shadow-sm"
        :class="isStudent ? 'grid-cols-2' : 'grid-cols-3'"
        role="tablist"
        aria-label="Kuis, arsip scan, dan statistik kelas"
      >
        <button
          type="button"
          role="tab"
          :aria-selected="activeClassTab === 'quizzes'"
          class="min-h-11 rounded-lg px-3 py-2 text-base font-semibold transition sm:min-h-12 sm:text-xl"
          :class="
            activeClassTab === 'quizzes'
              ? 'bg-[linear-gradient(90deg,#2563EB_0%,#808080_100%)] text-white shadow-sm'
              : 'text-[#808080] hover:bg-slate-50'
          "
          @click="selectClassTab('quizzes')"
        >
          Kuis
        </button>
        <button
          v-if="!isStudent"
          type="button"
          role="tab"
          :aria-selected="activeClassTab === 'archives'"
          class="min-h-11 rounded-lg px-2 py-2 text-sm font-semibold transition sm:min-h-12 sm:px-3 sm:text-xl"
          :class="
            activeClassTab === 'archives'
              ? 'bg-[linear-gradient(90deg,#2563EB_0%,#808080_100%)] text-white shadow-sm'
              : 'text-[#808080] hover:bg-slate-50'
          "
          @click="selectClassTab('archives')"
        >
          Arsip Scan
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="activeClassTab === 'statistics'"
          class="min-h-11 rounded-lg px-3 py-2 text-base font-semibold transition sm:min-h-12 sm:text-xl"
          :class="
            activeClassTab === 'statistics'
              ? 'bg-[linear-gradient(90deg,#2563EB_0%,#808080_100%)] text-white shadow-sm'
              : 'text-[#808080] hover:bg-slate-50'
          "
          @click="selectClassTab('statistics')"
        >
          Statistik
        </button>
      </div>

      <Transition name="tab-content" mode="out-in">
        <!-- Daftar Kuis -->
        <TransitionGroup
          v-if="activeClassTab === 'quizzes'"
          key="quiz-list"
          tag="section"
          name="quiz-card"
          appear
          class="space-y-4 sm:space-y-5"
        >
          <article
            v-for="(task, index) in tasks"
            :key="task.id"
            class="motion-surface group cursor-pointer rounded-2xl border border-[#f0f0f0] bg-white px-5 py-4 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:shadow-md sm:px-6 sm:py-5"
            :style="{ transitionDelay: `${Math.min(index, 5) * 55}ms` }"
            @click="handleTaskClick(task)"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <h2
                class="text-lg font-bold text-[#222222] transition group-hover:text-[#2864E8] sm:text-xl"
              >
                {{ task.title }}
              </h2>
              <p class="text-xs font-medium text-[#888888] sm:text-sm">
                Tenggat: {{ formatTaskDeadline(task) }}
              </p>
            </div>

            <div v-if="isStudent" class="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1">
              <span
                v-if="!getStudentSubmission(task)"
                class="text-xs font-semibold text-[#777777] sm:text-sm"
              >
                Belum dikerjakan
              </span>
              <template
                v-else-if="
                  getStudentSubmission(task).graded || getStudentSubmission(task).score != null
                "
              >
                <span class="text-xs font-semibold text-[#16834b] sm:text-sm"
                  >Sudah dikerjakan</span
                >
                <span
                  v-if="task.showScore !== false"
                  class="text-xs font-bold text-[#2864E8] sm:text-sm"
                >
                  Nilai: {{ getStudentSubmission(task).score }}/{{
                    getStudentSubmission(task).maxScore
                  }}
                </span>
              </template>
              <span v-else class="text-xs font-semibold text-[#b36b00] sm:text-sm">
                Menunggu nilai
              </span>
            </div>
          </article>
          <div
            v-if="tasks.length === 0"
            key="empty-state"
            class="rounded-2xl bg-white p-6 text-center text-sm text-[#888888] sm:p-8"
          >
            Belum ada kuis di kelas ini.
          </div>
        </TransitionGroup>

        <section
          v-else-if="activeClassTab === 'archives' && !isStudent"
          key="scan-archives"
          class="space-y-4 rounded-2xl bg-white p-4 shadow-sm sm:space-y-5 sm:p-6"
          aria-label="Arsip hasil scan"
        >
          <div v-if="!selectedArchiveFolder" class="space-y-4">
            <div>
              <h2 class="text-lg font-bold text-[#222222] sm:text-xl">Folder Arsip Scan</h2>
              <p class="mt-1 text-sm text-[#666666]">
                Foto lembar dan hasil koreksi yang sudah dikirim tersimpan di sini.
              </p>
            </div>
            <div class="space-y-3 sm:space-y-4">
              <button
                v-for="(folder, index) in archiveFolders"
                :key="folder.id"
                type="button"
                class="motion-surface group w-full rounded-2xl border border-[#f0f0f0] bg-white px-5 py-4 text-left shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-[#2864E8] hover:shadow-md sm:px-6 sm:py-5"
                :style="{ transitionDelay: `${Math.min(index, 5) * 55}ms` }"
                @click="selectedArchiveFolderId = folder.id"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="min-w-0">
                    <h3 class="truncate text-lg font-bold text-[#222222] transition group-hover:text-[#2864E8] sm:text-xl">
                      {{ folder.name }}
                    </h3>
                    <p class="mt-1 text-sm text-[#888888]">
                      {{ folder.archives?.length || 0 }} arsip
                    </p>
                  </div>
                  <svg class="size-5 shrink-0 text-[#888888]" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m9 18 6-6-6-6" />
                  </svg>
                </div>
              </button>
              <p
                v-if="archiveFolders.length === 0"
                class="rounded-2xl bg-slate-50 p-6 text-center text-sm text-[#888888] sm:p-8"
              >
                Belum ada arsip scan di kelas ini.
              </p>
            </div>
          </div>

          <div v-else class="space-y-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <button
                  type="button"
                  class="mb-2 flex items-center gap-1 text-sm font-semibold text-[#2864E8] hover:text-[#1f50be]"
                  @click="selectedArchiveFolderId = ''"
                >
                  <svg class="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m15 18-6-6 6-6" />
                  </svg>
                  Semua folder
                </button>
                <h2 class="text-lg font-bold text-[#222222] sm:text-xl">
                  {{ selectedArchiveFolder.name }}
                </h2>
              </div>
              <p class="text-sm text-[#888888]">
                {{ selectedArchiveFolder.archives?.length || 0 }} arsip
              </p>
            </div>

            <div class="space-y-3 sm:space-y-4">
              <button
                v-for="archive in selectedArchiveFolder.archives || []"
                :key="archive.id"
                type="button"
                class="group w-full rounded-2xl border border-[#f0f0f0] bg-white px-5 py-4 text-left shadow-sm transition hover:border-[#2864E8] hover:shadow-md sm:px-6 sm:py-5"
                @click="openArchive(archive)"
              >
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <h3 class="text-base font-bold text-[#222222] transition group-hover:text-[#2864E8] sm:text-lg">
                    {{ archive.title }}
                  </h3>
                  <span class="text-xs font-medium text-[#888888]">
                    {{ new Date(archive.createdAt).toLocaleDateString('id-ID') }}
                  </span>
                </div>
                <p class="mt-1 text-sm text-[#666666]">
                  {{ archive.studentName || archive.studentEmail }}
                  &bull; {{ archive.questions?.length || 0 }} soal
                </p>
              </button>
              <p
                v-if="selectedArchiveFolder.archives?.length === 0"
                class="rounded-2xl bg-slate-50 p-6 text-center text-sm text-[#888888] sm:p-8"
              >
                Folder ini belum memiliki arsip.
              </p>
            </div>
          </div>
        </section>

        <section
          v-else-if="!isStudent && !selectedStatisticStudent"
          key="student-list"
          class="rounded-2xl bg-white p-4 shadow-sm sm:p-6"
          aria-label="Statistik kelas"
        >
          <h2
            class="border-b border-[#d6d6d6] pb-2 text-lg font-semibold text-[#888888] sm:text-xl"
          >
            Mahasiswa
          </h2>
          <div class="mt-3 space-y-3 sm:space-y-4">
            <button
              v-for="student in classStatisticsStudents"
              :key="student.id"
              type="button"
              class="flex w-full min-w-0 cursor-pointer items-center gap-2 rounded-xl border border-[#c9c9c9] p-1.5 text-left shadow-[0_2px_3px_rgba(0,0,0,0.2)] transition hover:border-[#2864E8] hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#2864E8] sm:gap-3 sm:p-2"
              @click="selectedStatisticStudent = student"
            >
              <div
                class="size-14 shrink-0 overflow-hidden rounded-full bg-[#D9D9D9] sm:size-16"
              >
                <img
                  v-if="student.avatarUrl"
                  :src="student.avatarUrl"
                  :alt="`Foto profil ${student.name}`"
                  class="size-full object-cover"
                />
                <svg
                  v-else
                  class="size-full text-[#757575]"
                  viewBox="0 0 160 160"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  aria-hidden="true"
                >
                  <circle cx="80" cy="62" r="28" fill="currentColor" />
                  <path
                    d="M32 144C32 116 54 98 80 98C106 98 128 116 128 144"
                    fill="currentColor"
                  />
                </svg>
              </div>
              <div class="min-w-0 flex-1">
                <h3 class="truncate text-sm font-semibold text-[#777777] sm:text-base">
                  {{ student.name }}
                </h3>
                <p class="truncate text-[11px] text-[#888888] sm:text-xs">{{ student.email }}</p>
              </div>
              <div
                class="flex min-w-14 shrink-0 flex-col items-center rounded-lg bg-[#2864E8] px-2 py-1 text-xs font-medium leading-tight text-white shadow-sm sm:min-w-16 sm:py-1.5 sm:text-sm"
              >
                <span class="whitespace-nowrap text-[10px] sm:text-xs">Nilai rata-rata</span>
                <span>{{ student.average }}</span>
              </div>
            </button>
            <p
              v-if="classStatisticsStudents.length === 0"
              class="py-8 text-center text-sm text-[#888888]"
            >
              Belum ada mahasiswa.
            </p>
          </div>
        </section>

        <div v-else key="student-detail" class="space-y-4 sm:space-y-5">
          <section
            v-if="!isStudent"
            class="flex flex-wrap items-center justify-between gap-3 text-white"
          >
            <div>
              <p class="text-xs font-medium text-white/75">Statistik mahasiswa</p>
              <h2 class="mt-1 text-lg font-bold sm:text-xl">
                {{ visibleStatisticStudent.name }}
              </h2>
              <p class="text-xs text-white/80 sm:text-sm">{{ visibleStatisticStudent.email }}</p>
            </div>
            <button
              type="button"
              class="flex items-center gap-2 rounded-lg border border-white/60 px-3 py-2 text-sm font-medium text-white transition hover:bg-white/10"
              @click="selectedStatisticStudent = null"
            >
              <svg class="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 19l-7-7 7-7"
                />
              </svg>
              Kembali ke mahasiswa
            </button>
          </section>

          <section class="grid gap-3 sm:grid-cols-2 sm:gap-5" aria-label="Ringkasan nilai">
            <article class="rounded-xl bg-white px-4 py-6 text-center shadow-sm sm:py-7">
              <p class="text-lg font-bold text-[#2864E8] sm:text-2xl">
                JUMLAH KUIS: {{ statisticsTasks.length }}
              </p>
            </article>
            <article class="rounded-xl bg-white px-4 py-6 text-center shadow-sm sm:py-7">
              <p class="text-lg font-bold text-[#2864E8] sm:text-2xl">
                RATA-RATA: {{ visibleStatisticStudent.average }}
              </p>
            </article>
          </section>

          <section class="rounded-xl bg-white p-4 shadow-sm sm:p-6" aria-label="Nilai per kuis">
            <div class="overflow-x-auto">
              <div :style="{ minWidth: statisticChartWidth }">
                <div class="relative h-[260px] sm:h-[320px]">
                  <div
                    class="absolute inset-y-0 left-10 right-0 border-b border-l border-[#b9b9b9]"
                  >
                    <div
                      class="absolute inset-0 flex items-end justify-around gap-3 px-3 sm:gap-5 sm:px-5"
                    >
                      <div
                        v-for="quiz in visibleStatisticStudent.quizScores"
                        :key="quiz.id"
                        class="flex h-full min-w-0 flex-1 items-end justify-center"
                      >
                        <div
                          v-if="quiz.score !== null"
                          class="w-full max-w-[140px] rounded-t-sm bg-[#4f7fea] transition-[height] duration-500"
                          :style="{ height: getScoreHeight(quiz.score) }"
                          :title="`${quiz.title}: ${quiz.score}`"
                        />
                        <div v-else class="h-0 w-full max-w-[140px]" />
                      </div>
                    </div>
                  </div>
                  <div
                    v-for="tick in [0, 20, 40, 60, 80, 100]"
                    :key="tick"
                    class="pointer-events-none absolute left-10 right-0 border-t border-dotted border-[#dddddd]"
                    :style="{ top: `${100 - tick}%` }"
                  />
                  <div
                    v-for="tick in [0, 20, 40, 60, 80, 100]"
                    :key="`label-${tick}`"
                    class="pointer-events-none absolute left-0 w-8 text-right text-[10px] text-[#777777]"
                    :style="{
                      top: `${100 - tick}%`,
                      transform: `translateY(${tick === 100 ? '0' : tick === 0 ? '-100%' : '-50%'})`,
                    }"
                  >
                    {{ tick }}
                  </div>
                </div>
                <div
                  class="ml-10 grid gap-3 pt-2 text-center text-[10px] text-[#777777] sm:gap-5 sm:text-xs"
                  :style="{
                    gridTemplateColumns: `repeat(${Math.max(statisticsTasks.length, 1)}, minmax(0, 1fr))`,
                  }"
                >
                  <span
                    v-for="quiz in visibleStatisticStudent.quizScores"
                    :key="quiz.id"
                    class="truncate"
                  >
                    {{ quiz.title }}
                  </span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </Transition>

      <!-- Floating Action Button (FAB) Tambah Tugas (+) Sesuai Mockup Gambar -->
    </div>

    <Teleport to="body">
      <button
        v-if="!isStudent && activeClassTab === 'quizzes' && !selectedStatisticStudent"
        type="button"
        class="motion-control fixed bottom-20 right-6 z-30 flex size-14 cursor-pointer items-center justify-center rounded-full bg-white text-[#2864E8] shadow-[0_6px_20px_rgba(0,0,0,0.25)] transition duration-200 hover:scale-105 hover:shadow-[0_8px_25px_rgba(0,0,0,0.3)] active:scale-95 sm:bottom-8 sm:right-10 sm:size-16"
        aria-label="Tambah Tugas"
        @click="handleFabClick"
      >
        <svg class="size-8 sm:size-9" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2.5"
            d="M12 4v16m8-8H4"
          />
        </svg>
      </button>
    </Teleport>

    <!-- Modal Popup Pilihan: Buat Soal dengan AI atau Manual -->
    <Transition name="modal-fade">
      <div
        v-if="isChoiceModalOpen"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm"
        role="dialog"
        aria-modal="true"
        @click.self="isChoiceModalOpen = false"
      >
        <div
          class="w-full max-w-md overflow-hidden rounded-[28px] border border-[#e3e3e3] bg-white p-6 sm:p-8 shadow-2xl animate-scale-up"
        >
          <div class="flex items-center justify-between pb-3 border-b border-[#eee]">
            <div>
              <h3 class="text-lg font-bold text-[#222222] sm:text-xl">Buat Soal Kuis Baru</h3>
              <p class="text-xs text-[#777777] mt-0.5">
                Pilih metode pembuatan soal untuk kelas ini
              </p>
            </div>
            <button
              type="button"
              class="flex size-8 cursor-pointer items-center justify-center rounded-full text-[#666] hover:bg-gray-100 transition"
              @click="isChoiceModalOpen = false"
            >
              ✕
            </button>
          </div>

          <!-- Pilihan Opsi AI atau Manual -->
          <div class="mt-6 grid grid-cols-1 gap-3.5 sm:gap-4">
            <!-- Opsi 1: Buat Soal dengan AI (Rekomendasi Utama) -->
            <button
              type="button"
              class="motion-control group relative flex items-center gap-4 rounded-2xl border-2 border-[#2864E8] bg-blue-50/40 p-4 text-left transition duration-200 hover:bg-[#2864E8] hover:text-white hover:shadow-lg active:scale-[0.98] cursor-pointer"
              @click="handleChooseAi"
            >
              <!-- Ikon AI Sparkle / Generator -->
              <div
                class="flex size-12 shrink-0 items-center justify-center rounded-xl bg-[#2864E8] text-white shadow-sm transition group-hover:bg-white group-hover:text-[#2864E8]"
              >
                <svg class="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>

              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <h4 class="text-base font-bold text-[#222222] group-hover:text-white transition">
                    Buat Soal dengan AI
                  </h4>
                  <span
                    class="rounded-full bg-[#2864E8] px-2 py-0.5 text-[10px] font-semibold text-white group-hover:bg-white group-hover:text-[#2864E8] transition"
                  >
                    Cepat
                  </span>
                </div>
                <p class="mt-0.5 text-xs text-[#666666] group-hover:text-white/90 transition">
                  Ketik topik atau materi, AI akan otomatis menghasilkan butir soal esai & pilihan
                  ganda.
                </p>
              </div>

              <!-- Panah Kanan -->
              <svg
                class="size-5 shrink-0 text-[#2864E8] group-hover:text-white group-hover:translate-x-1 transition"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2.5"
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>

            <!-- Opsi 2: Buat Soal Manual -->
            <button
              type="button"
              class="motion-control group flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 text-left transition duration-200 hover:border-slate-300 hover:bg-slate-50 hover:shadow-md active:scale-[0.98] cursor-pointer"
              @click="handleChooseManual"
            >
              <div
                class="flex size-12 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-[#555] transition group-hover:bg-[#2864E8] group-hover:text-white"
              >
                <svg class="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
                </svg>
              </div>

              <div class="min-w-0 flex-1">
                <h4 class="text-base font-bold text-[#333333]">Buat Soal Manual</h4>
                <p class="mt-0.5 text-xs text-[#777777]">
                  Tulis judul tugas dan butir soal secara langsung tanpa bantuan generator AI.
                </p>
              </div>

              <svg
                class="size-5 shrink-0 text-slate-400 group-hover:text-[#2864E8] group-hover:translate-x-1 transition"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2.5"
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Modal Tambah Tugas Sederhana -->
    <Transition name="modal-fade">
      <div
        v-if="isAddTaskModalOpen"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm"
        role="dialog"
        aria-modal="true"
      >
        <div class="w-full max-w-md rounded-[28px] border border-[#e3e3e3] bg-white p-6 shadow-2xl">
          <div class="flex items-center justify-between pb-3 border-b border-[#eee]">
            <h3 class="text-lg font-bold text-[#222222]">Tambah Tugas Baru</h3>
            <button
              type="button"
              class="flex size-7 cursor-pointer items-center justify-center rounded-full text-[#666] hover:bg-gray-100"
              @click="closeAddTaskModal"
            >
              ✕
            </button>
          </div>

          <div class="mt-4 space-y-4">
            <div>
              <label class="block text-xs font-semibold text-[#555] mb-1">Judul Tugas</label>
              <input
                v-model="newTaskTitle"
                type="text"
                placeholder="Contoh: Tugas 3"
                class="w-full rounded-xl border border-[#ccc] px-3.5 py-2.5 text-sm outline-none focus:border-[#2864E8]"
              />
            </div>
            <div>
              <label class="block text-xs font-semibold text-[#555] mb-1"
                >Catatan / Deskripsi (Opsional)</label
              >
              <textarea
                v-model="newTaskDesc"
                rows="3"
                placeholder="Instruksi tugas atau materi terkait..."
                class="w-full rounded-xl border border-[#ccc] px-3.5 py-2.5 text-sm outline-none focus:border-[#2864E8]"
              />
            </div>
          </div>

          <div class="mt-6 flex justify-end gap-3">
            <button
              type="button"
              class="rounded-full px-5 py-2 text-xs font-semibold text-[#666] hover:bg-gray-100"
              @click="closeAddTaskModal"
            >
              Batal
            </button>
            <button
              type="button"
              class="rounded-full bg-[#2864E8] px-6 py-2 text-xs font-semibold text-white shadow hover:bg-[#1f50be]"
              @click="handleAddTask"
            >
              Simpan Tugas
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <Teleport to="body">
      <div
        v-if="selectedArchive"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-3 backdrop-blur-sm sm:p-6"
        @click.self="closeArchive"
      >
        <section
          class="flex max-h-[calc(100dvh-24px)] w-full max-w-4xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl sm:max-h-[calc(100dvh-48px)]"
          role="dialog"
          aria-modal="true"
          aria-labelledby="scan-archive-title"
        >
          <header class="flex shrink-0 items-center justify-between gap-4 bg-[linear-gradient(105deg,#2864E8_0%,#173C87_100%)] px-5 py-4 text-white sm:px-7">
            <div class="min-w-0">
              <h2 id="scan-archive-title" class="truncate text-lg font-bold sm:text-2xl">
                {{ selectedArchive.title }}
              </h2>
              <p class="mt-1 truncate text-xs text-white/80 sm:text-sm">
                {{ selectedArchive.studentName || selectedArchive.studentEmail }} &bull;
                {{ new Date(selectedArchive.createdAt).toLocaleString('id-ID') }}
              </p>
            </div>
            <button
              type="button"
              class="flex size-9 shrink-0 items-center justify-center rounded-full text-white/90 transition hover:bg-white/10 hover:text-white"
              aria-label="Tutup arsip scan"
              @click="closeArchive"
            >
              <svg class="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 6l12 12M18 6 6 18" />
              </svg>
            </button>
          </header>
          <div class="min-h-0 space-y-5 overflow-y-auto p-4 sm:p-7">
            <section class="rounded-xl border border-slate-200 bg-slate-50 p-3 sm:p-4">
              <h3 class="mb-3 text-sm font-bold text-[#333333] sm:text-base">Foto lembar asli</h3>
              <p v-if="isLoadingArchiveImage" class="py-8 text-center text-sm text-[#666666]">
                Membuka foto arsip...
              </p>
              <p v-else-if="archiveImageError" role="alert" class="py-4 text-sm text-red-600">
                {{ archiveImageError }}
              </p>
              <img
                v-else-if="archiveImageUrl"
                :src="archiveImageUrl"
                alt="Foto asli lembar scan"
                class="mx-auto max-h-[55vh] w-auto max-w-full rounded-lg object-contain"
              />
            </section>

            <section>
              <h3 class="mb-3 text-sm font-bold text-[#333333] sm:text-base">Hasil koreksi</h3>
              <div class="space-y-3">
                <article
                  v-for="(question, index) in selectedArchive.questions"
                  :key="`${selectedArchive.id}-${index}`"
                  class="rounded-xl border border-slate-200 p-4"
                >
                  <div class="flex flex-wrap items-start justify-between gap-2">
                    <h4 class="min-w-0 flex-1 text-sm font-semibold text-[#222222]">
                      {{ index + 1 }}. {{ question.title }}
                    </h4>
                    <span class="shrink-0 rounded-full bg-blue-50 px-2.5 py-1 text-xs font-bold text-[#2864E8]">
                      {{ question.score }} / {{ question.points }}
                    </span>
                  </div>
                  <div class="mt-3 grid gap-2 text-sm sm:grid-cols-2">
                    <p class="text-[#666666]">
                      Jawaban terbaca:
                      <strong class="text-[#222222]">
                        {{ question.options?.find((option) => option.value === question.selectedOption)?.label || 'Kosong' }}
                      </strong>
                    </p>
                    <p class="text-[#666666]">
                      Kunci jawaban:
                      <strong class="text-[#222222]">
                        {{ question.options?.find((option) => option.value === question.answerKey)?.label || question.answerKey }}
                      </strong>
                    </p>
                  </div>
                  <p class="mt-2 text-xs text-[#888888]">
                    Nilai AI: {{ question.aiScore }} / {{ question.points }}
                  </p>
                </article>
              </div>
              <p class="mt-3 text-right text-sm font-bold text-[#2864E8]">
                Total:
                {{ selectedArchive.questions?.reduce((total, question) => total + (Number(question.score) || 0), 0) || 0 }}
                / {{ selectedArchive.questions?.reduce((total, question) => total + (Number(question.points) || 0), 0) || 0 }}
                poin
              </p>
            </section>
          </div>
        </section>
      </div>
    </Teleport>
  </DashboardLayout>
</template>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.quiz-card-enter-active,
.quiz-card-leave-active,
.quiz-card-move {
  transition:
    opacity 0.35s ease,
    transform 0.35s cubic-bezier(0.2, 0.7, 0.2, 1);
}

.quiz-card-enter-from,
.quiz-card-leave-to {
  opacity: 0;
  transform: translateY(14px) scale(0.99);
}

.tab-content-enter-active,
.tab-content-leave-active {
  transition:
    opacity 0.24s ease,
    transform 0.24s ease;
}

.tab-content-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.tab-content-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (prefers-reduced-motion: reduce) {
  .quiz-card-enter-active,
  .quiz-card-leave-active,
  .quiz-card-move,
  .tab-content-enter-active,
  .tab-content-leave-active {
    transition: none;
  }
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
  animation: scaleUp 0.22s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>
