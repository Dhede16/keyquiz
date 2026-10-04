<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import {
  classes,
  saveTaskSubmission,
  updateSubmissionScore,
  updateTaskSettings,
} from '@/composables/useClasses.js'
import DashboardLayout from '@/layouts/DashboardLayout.vue'
import QuizSheetTabs from '@/components/ui/QuizSheetTabs.vue'
import StudentAvatar from '@/components/icons/StudentAvatar.vue'
import { defaultStudents } from '@/data/students.js'
import taskBannerImg from '@/assets/images/BennerMengerjakan.png'


const route = useRoute()
const router = useRouter()
const { user } = useAuth()

const classId = computed(() => route.params.id || 1)
const taskId = computed(() => route.params.taskId || 1)
const isStudent = computed(() => user.value?.role === 'student')
const activeSheet = ref('results')

const currentClass = computed(() => {
  return classes.value.find((c) => String(c.id) === String(classId.value)) || classes.value[0]
})

const currentTask = computed(() => {
  const tasks = currentClass.value?.tasks || []
  return (
    tasks.find((t) => String(t.id) === String(taskId.value)) || {
      id: taskId.value,
      title: `Tugas ${taskId.value}`,
      date: 'Senin, 28 September 2026',
    }
  )
})

const questions = computed(() => currentTask.value.questions || [])
const answers = ref([])
const isSubmissionSuccessOpen = ref(false)

const studentSubmission = computed(() => {
  const email = user.value?.email?.trim().toLowerCase()
  if (!email) return null

  return (
    currentTask.value.submissions?.find(
      (submission) => submission.email?.trim().toLowerCase() === email,
    ) || null
  )
})

const submissions = computed(() => currentTask.value.submissions || [])
const resultStudents = computed(() =>
  submissions.value.length > 0
    ? submissions.value.map((submission) => ({
        ...submission,
        isDemo: false,
        displayScore: submission.graded ? submission.score : 'Belum',
      }))
    : defaultStudents.map((student) => ({
        ...student,
        isDemo: true,
        displayScore: student.score,
      })),
)
const maxScore = computed(() =>
  questions.value.reduce((total, question) => total + (Number(question.points) || 0), 0),
)
const canSubmit = computed(
  () =>
    questions.value.length > 0 &&
    Boolean(user.value?.email) &&
    answers.value.length === questions.value.length &&
    answers.value.every((answer) => answer.trim()),
)

watch(
  questions,
  (taskQuestions) => {
    if (!studentSubmission.value) answers.value = taskQuestions.map(() => '')
  },
  { immediate: true },
)

function normalizeAnswer(answer) {
  return String(answer || '')
    .trim()
    .replace(/\s+/g, ' ')
    .toLocaleLowerCase()
}

function getSubmittedAnswer(question, index) {
  return (
    studentSubmission.value?.answers?.find((answer) => answer.questionId === question.id)?.value ??
    studentSubmission.value?.answers?.[index]?.value ??
    ''
  )
}

function isAnswerCorrect(question, answer) {
  return (
    Boolean(question.answerKey?.trim()) &&
    normalizeAnswer(answer) === normalizeAnswer(question.answerKey)
  )
}

const isSubmitting = ref(false)

async function submitAnswers() {
  if (!canSubmit.value || !user.value?.email || isSubmitting.value) return

  isSubmitting.value = true
  const submittedAnswers = questions.value.map((question, index) => ({
    questionId: question.id,
    value: answers.value[index].trim(),
    score: null,
    aiEvaluation: null,
  }))

  // Jawaban tersimpan, nilai null — menunggu koreksi dosen
  const savedTask = await saveTaskSubmission(currentClass.value.id, currentTask.value.id, {
    email: user.value.email,
    name: user.value.name,
    answers: submittedAnswers,
    score: null,
    maxScore: maxScore.value,
    graded: false,
    submittedAt: new Date().toISOString(),
  })

  isSubmitting.value = false
  if (savedTask) isSubmissionSuccessOpen.value = true
}

function saveSettings(key, event) {
  updateTaskSettings(classId.value, taskId.value, { [key]: event.target.checked })
}

function openStudentResult(student) {
  if (student.isDemo) return
  router.push({
    name: 'grade-submission',
    params: { id: String(classId.value), taskId: String(taskId.value) },
    query: { studentEmail: student.email },
  })
}
</script>

<template>
  <DashboardLayout>
    <div class="space-y-4 pb-16 sm:space-y-6 sm:pb-20">
      <!-- Breadcrumb Navigasi Kembali -->
      <div v-if="!isStudent" class="flex items-center gap-2 text-white/90">
        <button
          type="button"
          class="flex items-center gap-1.5 text-xs font-medium text-white/80 transition hover:text-white sm:text-sm"
          @click="router.push(`/kelas/${classId}`)"
        >
          <svg class="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2.5"
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Kembali ke Detail Kelas
        </button>
      </div>

      <section
        class="overflow-hidden rounded-[1.5rem] border-4 border-white bg-white shadow-sm sm:rounded-[2rem]"
      >
        <img
          :src="taskBannerImg"
          alt="Mengerjakan soal"
          class="block aspect-[4.7/1] w-full object-cover"
        />
      </section>

      <section class="rounded-2xl bg-white px-4 py-3 shadow-sm sm:px-5 sm:py-4">
        <template v-if="isStudent">
          <h1 class="text-lg font-bold leading-snug text-[#222222] sm:text-xl">
            {{ currentTask.title }}
          </h1>
          <div class="my-1.5 h-px w-full bg-[#bdbdbd]"></div>
          <p class="text-sm text-[#888888] sm:text-base">
            {{ currentTask.description || `Pertanyaan seputar ${currentTask.title}` }}
          </p>
        </template>
        <template v-else>
          <div class="flex flex-wrap items-center gap-x-2 gap-y-1">
            <span
              class="inline-flex rounded-full bg-[#2864E8]/10 px-2 py-0.5 text-[10px] font-semibold text-[#2864E8] sm:text-xs"
            >
              {{ currentClass.major || 'Teknik Informatika' }}
            </span>
            <p class="text-[10px] font-medium text-[#777777] sm:text-xs">
              Pengajar: {{ currentClass.lecturer || 'Fajerin Abdillah, M. Kom.' }} &bull;
              {{ currentTask.date }}
            </p>
          </div>
          <h1 class="mt-1.5 text-base font-bold leading-snug text-[#222222] sm:text-lg">
            {{ currentTask.title }}
            <span class="font-medium text-[#777777]">&bull; {{ currentClass.title }}</span>
          </h1>
        </template>
      </section>

      <section
        v-if="isStudent && questions.length === 0"
        class="rounded-[1.5rem] bg-white p-6 text-sm text-[#777777] shadow-sm sm:rounded-[2rem] sm:p-8"
      >
        Dosen belum menambahkan soal pada tugas ini.
      </section>

      <form
        v-else-if="isStudent && !studentSubmission"
        class="space-y-4"
        @submit.prevent="submitAnswers"
      >
        <section
          v-for="(question, index) in questions"
          :key="question.id"
          class="motion-surface flex flex-col rounded-[1.5rem] bg-white p-5 shadow-sm sm:rounded-[2rem] sm:p-8"
        >
          <h2 class="text-base font-medium leading-snug text-[#222222] sm:text-lg">
            {{ question.title }}
          </h2>
          <div class="my-2 h-px w-full bg-[#bdbdbd]"></div>

          <div v-if="question.type === 'multiple_choice'" class="space-y-1">
            <label
              v-for="(option, optionIndex) in question.options"
              :key="optionIndex"
              class="flex cursor-pointer items-center gap-2.5 py-0.5 text-sm text-[#222222] transition-colors sm:text-base"
            >
              <input
                v-model="answers[index]"
                type="radio"
                :name="`question-${question.id}`"
                :value="option"
                class="size-3.5 shrink-0 accent-[#2864E8]"
              />
              <span>{{ option }}</span>
            </label>
          </div>
          <div v-else class="space-y-0.5">
            <label :for="`answer-${question.id}`" class="text-xs text-[#888888] sm:text-sm">
              Jawaban:
            </label>
            <textarea
              :id="`answer-${question.id}`"
              v-model="answers[index]"
              rows="1"
              class="w-full resize-y border-b border-transparent bg-transparent py-0 text-sm font-medium text-[#222222] outline-none focus:border-[#2864E8] sm:text-base"
              placeholder="Tulis jawaban kamu"
            />
          </div>
          <p class="mt-2 self-end text-[10px] text-[#888888]">{{ question.points }} Poin*</p>
        </section>

        <div class="flex justify-end">
          <button
            type="submit"
            :disabled="!canSubmit"
            class="motion-control rounded-xl border border-white/80 bg-transparent px-10 py-3 text-base font-semibold text-white transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50 sm:px-12 sm:py-3.5 sm:text-lg"
          >
            Kirim
          </button>
        </div>
      </form>

      <section
        v-else-if="isStudent"
        class="space-y-4 rounded-[1.5rem] bg-white p-5 shadow-sm sm:rounded-[2rem] sm:p-8"
      >
        <div
          class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4"
        >
          <div>
            <h2 class="text-lg font-bold text-[#333333]">Jawaban kamu</h2>
            <p class="mt-1 text-sm text-[#777777]">
              {{
                studentSubmission.graded
                  ? 'Tugas sudah dinilai oleh dosen.'
                  : 'Tugas terkumpul. Menunggu koreksi dosen.'
              }}
            </p>
          </div>
          <!-- Nilai hanya tampil setelah dosen melakukan koreksi -->
          <p
            v-if="studentSubmission.graded && currentTask.showScore !== false"
            class="text-lg font-bold text-[#2864E8]"
          >
            Nilai {{ studentSubmission.score }}/{{ studentSubmission.maxScore }}
          </p>
          <span
            v-else-if="!studentSubmission.graded"
            class="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-700"
          >
            <svg class="size-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Menunggu koreksi
          </span>
        </div>

        <article
          v-for="(question, index) in questions"
          :key="question.id"
          class="border-b border-slate-100 py-3 last:border-0"
        >
          <p class="font-semibold text-[#333333]">{{ question.title }}</p>
          <p class="mt-2 text-sm text-[#666666]">
            Jawaban kamu: {{ getSubmittedAnswer(question, index) }}
          </p>
          <template v-if="studentSubmission.graded && currentTask.showCorrectAnswers && question.answerKey">
            <p
              class="mt-2 text-sm font-semibold"
              :class="
                isAnswerCorrect(question, getSubmittedAnswer(question, index))
                  ? 'text-emerald-700'
                  : 'text-red-600'
              "
            >
              {{
                isAnswerCorrect(question, getSubmittedAnswer(question, index))
                  ? 'Benar'
                  : 'Belum tepat'
              }}
            </p>
            <p class="mt-1 text-sm text-[#666666]">Kunci jawaban: {{ question.answerKey }}</p>
          </template>
        </article>
      </section>

      <Teleport to="body">
        <Transition name="submission-success">
          <div
            v-if="isSubmissionSuccessOpen"
            class="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4 backdrop-blur-sm"
            @click.self="isSubmissionSuccessOpen = false"
          >
            <section
              class="submission-success-card w-full max-w-md rounded-3xl bg-white px-6 py-8 text-center shadow-2xl sm:px-9 sm:py-10"
              role="dialog"
              aria-modal="true"
              aria-labelledby="submission-success-title"
              aria-describedby="submission-success-description"
            >
              <div
                class="success-check mx-auto flex size-[76px] items-center justify-center rounded-full bg-emerald-100 text-emerald-600 sm:size-20"
                aria-hidden="true"
              >
                <svg class="size-10 sm:size-11" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2.5"
                    d="m5 12 4 4L19 6"
                  />
                </svg>
              </div>
              <p
                class="mt-5 inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700"
              >
                Kuis berhasil dikirim
              </p>
              <h2
                id="submission-success-title"
                class="mt-3 text-xl font-bold text-[#222222] sm:text-2xl"
              >
                Kamu sudah mengerjakan kuis ini!
              </h2>
              <p id="submission-success-description" class="mt-2 text-sm text-[#666666] sm:text-base">
                Jawabanmu sudah tersimpan. Terima kasih sudah menyelesaikan
                <strong>{{ currentTask.title }}</strong>.
              </p>
              <button
                type="button"
                class="motion-control mt-7 w-full rounded-xl bg-[#2864E8] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#1f50be] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#2864E8] sm:text-base"
                @click="isSubmissionSuccessOpen = false"
              >
                Lihat jawaban saya
              </button>
            </section>
          </div>
        </Transition>
      </Teleport>

      <template v-if="!isStudent">
        <QuizSheetTabs :active-tab="activeSheet" @select="activeSheet = $event" />

        <div v-if="activeSheet === 'questions'" class="space-y-4 sm:space-y-5">
          <section
            v-if="questions.length === 0"
            class="rounded-[1.5rem] bg-white p-6 text-sm text-[#777777] shadow-sm sm:rounded-[2rem] sm:p-8"
          >
            Dosen belum menambahkan soal pada tugas ini.
          </section>

          <article
            v-for="(question, index) in questions"
            :key="question.id"
            class="space-y-4 rounded-[1.5rem] border border-[#f0f0f0] bg-white p-5 shadow-sm sm:rounded-[2rem] sm:p-8"
          >
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div class="min-w-0 flex-1">
                <p class="text-xs font-semibold text-[#2563EB]">
                  Soal {{ index + 1 }} · {{ question.points }} poin
                </p>
                <h3
                  class="mt-2 border-b border-[#e5e5e5] pb-2 text-base font-semibold text-[#333333] sm:text-lg"
                >
                  {{ question.title }}
                </h3>
              </div>
              <span
                class="inline-flex w-fit shrink-0 items-center rounded-xl border border-[#cccccc] px-4 py-2 text-xs font-semibold text-[#555555] sm:text-sm"
              >
                {{
                  question.type === 'multiple_choice' ? 'Pilihan Ganda' : 'Esai / Jawaban Singkat'
                }}
              </span>
            </div>

            <div v-if="question.type === 'multiple_choice'" class="space-y-3">
              <div
                v-for="(option, optionIndex) in question.options"
                :key="optionIndex"
                class="flex items-center gap-3 text-sm text-[#444444] sm:text-base"
              >
                <span class="size-4 shrink-0 rounded-full border-2 border-[#888888]" />
                <span>{{ option }}</span>
              </div>
            </div>
            <div v-else class="border-b border-[#cccccc] pb-1 text-sm text-[#888888]">
              Teks Jawaban
            </div>

            <p v-if="question.answerKey" class="text-xs font-medium text-[#16834b]">
              Kunci jawaban: {{ question.answerKey }}
            </p>
          </article>
        </div>

        <template v-else>
          <section class="rounded-[1.5rem] bg-white p-5 shadow-sm sm:rounded-[2rem] sm:p-8">
            <h2 class="text-lg font-bold text-[#333333]">Pengaturan hasil siswa</h2>
            <div class="mt-4 grid gap-3 sm:grid-cols-2">
              <label class="flex items-start gap-2 text-sm text-[#555555]">
                <input
                  type="checkbox"
                  :checked="currentTask.showScore !== false"
                  class="mt-0.5 accent-[#2864E8]"
                  @change="saveSettings('showScore', $event)"
                />
                <span>Tampilkan nilai kepada siswa</span>
              </label>
              <label class="flex items-start gap-2 text-sm text-[#555555]">
                <input
                  type="checkbox"
                  :checked="currentTask.showCorrectAnswers === true"
                  class="mt-0.5 accent-[#2864E8]"
                  @change="saveSettings('showCorrectAnswers', $event)"
                />
                <span>Tampilkan kunci dan benar/salah</span>
              </label>
            </div>
          </section>

          <section class="rounded-[1.5rem] bg-white p-5 shadow-sm sm:rounded-[2rem] sm:p-8">
            <h2 class="text-lg font-bold text-[#333333]">Mahasiswa</h2>
            <div
              class="mt-4 grid gap-3 border-t border-[#d6d6d6] pt-4 sm:grid-cols-2 sm:gap-4 lg:gap-x-8"
            >
              <article v-for="student in resultStudents" :key="student.email" class="min-w-0">
                <button
                  type="button"
                  :disabled="student.isDemo"
                  class="flex w-full min-w-0 cursor-pointer items-center gap-2 rounded-xl border border-[#c9c9c9] p-1.5 text-left shadow-[0_2px_3px_rgba(0,0,0,0.2)] transition hover:border-[#2864E8] hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#2864E8] disabled:cursor-default sm:gap-3 sm:p-2"
                  @click="openStudentResult(student)"
                >
                  <div class="size-14 shrink-0 overflow-hidden rounded-xl sm:size-16">
                    <StudentAvatar />
                  </div>
                  <div class="min-w-0 flex-1">
                    <h3 class="truncate text-sm font-semibold text-[#777777] sm:text-base">
                      {{ student.name || student.email }}
                    </h3>
                    <p class="truncate text-[11px] text-[#888888] sm:text-xs">
                      {{ student.email }}
                    </p>
                    <p v-if="!student.isDemo" class="mt-0.5 text-[10px] font-medium text-[#2864E8]">
                      {{ student.graded ? 'Sudah dinilai · Klik untuk lihat' : 'Belum dinilai · Klik untuk koreksi' }}
                    </p>
                  </div>
                  <div
                    class="flex min-w-14 shrink-0 flex-col items-center rounded-lg px-2 py-1 text-xs font-medium leading-tight text-white shadow-sm sm:min-w-16 sm:py-1.5 sm:text-sm"
                    :class="student.graded ? 'bg-emerald-500' : 'bg-[#2864E8]'"
                  >
                    <span>Nilai</span>
                    <span>{{ student.displayScore }}</span>
                  </div>
                </button>
              </article>
            </div>
          </section>
        </template>
      </template>
    </div>
  </DashboardLayout>
</template>

<style scoped>
.submission-success-enter-active,
.submission-success-leave-active {
  transition: opacity 180ms ease;
}

.submission-success-enter-active .submission-success-card,
.submission-success-leave-active .submission-success-card {
  transition: transform 220ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.submission-success-enter-from,
.submission-success-leave-to {
  opacity: 0;
}

.submission-success-enter-from .submission-success-card,
.submission-success-leave-to .submission-success-card {
  transform: translateY(14px) scale(0.96);
}

.submission-success-enter-active .success-check {
  animation: success-pop 420ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

@keyframes success-pop {
  0% {
    transform: scale(0.65);
    opacity: 0;
  }
  70% {
    transform: scale(1.08);
    opacity: 1;
  }
  100% {
    transform: scale(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .submission-success-enter-active,
  .submission-success-leave-active,
  .submission-success-enter-active .submission-success-card,
  .submission-success-leave-active .submission-success-card,
  .submission-success-enter-active .success-check {
    animation: none !important;
    transition: none !important;
  }
}
</style>
