<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DashboardLayout from '@/layouts/DashboardLayout.vue'
import { classes, updateSubmissionScore } from '@/composables/useClasses.js'
import taskBannerImg from '@/assets/images/BennerMengerjakan.png'

const route = useRoute()
const router = useRouter()

const classId = computed(() => route.params.id)
const taskId = computed(() => route.params.taskId)
const studentEmail = computed(() => route.query.studentEmail || '')

const currentClass = computed(
  () => classes.value.find((c) => String(c.id) === String(classId.value)) || classes.value[0],
)

const currentTask = computed(() =>
  (currentClass.value?.tasks || []).find((t) => String(t.id) === String(taskId.value)) || null,
)

const submission = computed(() => {
  const email = studentEmail.value.trim().toLowerCase()
  return (
    currentTask.value?.submissions?.find((s) => s.email?.trim().toLowerCase() === email) || null
  )
})

const questions = computed(() => currentTask.value?.questions || [])

const scoreDrafts = ref({})

watch(
  [submission, questions],
  ([s]) => {
    if (!s) return
    const draft = {}
    for (const q of questions.value) {
      const ans = s.answers?.find((a) => a.questionId === q.id)
      if (ans?.score != null) {
        // Sudah pernah dinilai — pakai nilai yang ada
        draft[q.id] = String(ans.score)
      } else if (q.answerKey?.trim() && ans?.value) {
        // Auto-fill: benar → poin penuh, salah → 0
        const correct = ans.value.trim().toLowerCase() === q.answerKey.trim().toLowerCase()
        draft[q.id] = correct ? String(Number(q.points) || 0) : '0'
      } else {
        draft[q.id] = ''
      }
    }
    scoreDrafts.value = draft
  },
  { immediate: true },
)

const totalInput = computed(() =>
  questions.value.reduce((sum, q) => {
    const v = Number(scoreDrafts.value[q.id])
    return sum + (Number.isFinite(v) ? v : 0)
  }, 0),
)

const maxScore = computed(() =>
  questions.value.reduce((sum, q) => sum + (Number(q.points) || 0), 0),
)

const isSubmitting = ref(false)
const isDone = ref(false)

async function submitGrade() {
  if (isSubmitting.value || !submission.value) return
  isSubmitting.value = true
  const bounded = Math.min(Math.max(totalInput.value, 0), maxScore.value)
  await updateSubmissionScore(classId.value, taskId.value, studentEmail.value, bounded)
  isSubmitting.value = false
  isDone.value = true
}

function getStudentAnswer(question) {
  return submission.value?.answers?.find((a) => a.questionId === question.id)?.value || '-'
}

function isAnswerCorrect(question) {
  const ans = getStudentAnswer(question)
  if (!question.answerKey?.trim() || ans === '-') return null
  return ans.trim().toLowerCase() === question.answerKey.trim().toLowerCase()
}
</script>

<template>
  <DashboardLayout :no-scroll="true">
    <div class="flex h-full min-h-0 flex-1 flex-col">
      <!-- Breadcrumb -->
      <div class="flex shrink-0 items-center justify-between pb-3 text-white/90 sm:pb-3.5">
        <button
          type="button"
          class="flex cursor-pointer items-center gap-1.5 text-xs font-semibold text-white/90 transition hover:-translate-x-0.5 hover:text-white sm:text-sm"
          @click="router.push(`/kelas/${classId}/tugas/${taskId}`)"
        >
          <svg class="size-4 sm:size-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" />
          </svg>
          Kembali ke Hasil Kuis
        </button>

        <button
          v-if="!isDone && submission && !submission.graded"
          type="button"
          :disabled="isSubmitting"
          class="motion-control cursor-pointer rounded-xl bg-white px-4 py-1.5 text-xs font-bold text-[#2864E8] shadow-sm transition hover:bg-white/90 active:scale-95 disabled:opacity-50 sm:text-sm"
          @click="submitGrade"
        >
          {{ isSubmitting ? 'Mengirim...' : 'Kirim Nilai' }}
        </button>
        <span
          v-else-if="isDone || submission?.graded"
          class="inline-flex items-center gap-1.5 rounded-xl bg-emerald-500 px-3 py-1.5 text-xs font-bold text-white"
        >
          <svg class="size-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="m5 12 4 4L19 6" />
          </svg>
          Nilai Terkirim
        </span>
      </div>

      <!-- Konten Scrollable -->
      <div class="relative min-h-0 flex-1 space-y-4 overflow-y-auto pb-24 pr-1 sm:space-y-5">
        <!-- Banner -->
        <section
          class="shrink-0 overflow-hidden rounded-[1.5rem] border-4 border-white bg-white shadow-sm sm:rounded-[2rem]"
        >
          <img
            :src="taskBannerImg"
            alt="Koreksi jawaban"
            class="block aspect-[4.7/1] w-full select-none object-cover"
          />
        </section>

        <!-- Tidak ada submission -->
        <section
          v-if="!submission"
          class="rounded-[1.5rem] bg-white p-8 text-center text-sm text-[#888888] shadow-sm sm:rounded-[2rem]"
        >
          Data jawaban mahasiswa tidak ditemukan.
        </section>

        <template v-else>
          <!-- Header Identitas Mahasiswa -->
          <section
            class="space-y-1 rounded-[1.5rem] border border-[#e3e3e3] bg-white p-6 shadow-sm sm:rounded-[2rem] sm:p-8 lg:p-9"
          >
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p class="text-xs font-semibold uppercase tracking-wide text-[#2864E8]">
                  Lembar Koreksi Jawaban
                </p>
                <h1 class="mt-1 text-xl font-bold text-[#222222] sm:text-2xl">
                  {{ submission.name || submission.email }}
                </h1>
                <p class="mt-0.5 text-sm text-[#888888]">{{ submission.email }}</p>
                <p class="mt-0.5 text-xs text-[#aaaaaa]">
                  {{ currentTask?.title }} &bull; {{ currentClass?.title }}
                </p>
              </div>

              <div class="flex flex-col items-end gap-2">
                <span
                  v-if="isDone || submission.graded"
                  class="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700"
                >
                  <svg class="size-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="m5 12 4 4L19 6" />
                  </svg>
                  Sudah dinilai
                </span>
                <span
                  v-else
                  class="inline-flex items-center gap-1 rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700"
                >
                  <svg class="size-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Menunggu koreksi
                </span>
                <p class="text-sm font-bold text-[#2864E8]">
                  {{ totalInput }} <span class="text-xs font-normal text-[#aaaaaa]">/ {{ maxScore }} poin</span>
                </p>
              </div>
            </div>
          </section>

          <!-- Kartu per-soal -->
          <TransitionGroup tag="div" name="question-card" appear class="space-y-4">
            <section
              v-for="(question, qIndex) in questions"
              :key="question.id"
              class="motion-surface group relative space-y-5 rounded-[1.5rem] border border-[#e3e3e3] bg-white p-6 shadow-sm transition hover:shadow-md sm:rounded-[2rem] sm:p-8 lg:p-9"
              :style="{ transitionDelay: `${Math.min(qIndex, 4) * 60}ms` }"
            >
              <!-- Header Soal -->
              <div>
                <p class="text-xs font-semibold text-[#2563EB]">
                  Soal {{ qIndex + 1 }} &bull;
                  {{ question.type === 'multiple_choice' ? 'Pilihan Ganda' : 'Esai / Jawaban Singkat' }}
                  &bull; {{ question.points }} poin
                </p>
                <h2 class="mt-2 border-b border-[#e5e5e5] pb-2 text-base font-bold text-[#333333] sm:text-lg">
                  {{ question.title }}
                </h2>
              </div>

              <!-- Opsi Pilihan Ganda -->
              <div v-if="question.type === 'multiple_choice'" class="space-y-2">
                <div
                  v-for="(opt, optIdx) in question.options"
                  :key="optIdx"
                  class="flex items-center gap-3 rounded-xl border px-3 py-2.5 text-sm transition"
                  :class="{
                    // Opsi yang dipilih mahasiswa — benar → biru, salah → merah
                    'border-blue-400 bg-blue-50 font-semibold text-blue-800':
                      opt.trim().toLowerCase() === getStudentAnswer(question).trim().toLowerCase() &&
                      isAnswerCorrect(question) === true,
                    'border-red-400 bg-red-50 font-semibold text-red-800':
                      opt.trim().toLowerCase() === getStudentAnswer(question).trim().toLowerCase() &&
                      isAnswerCorrect(question) === false,
                    // Kunci jawaban yang benar (selalu ditandai hijau)
                    'border-emerald-400 bg-emerald-50 font-semibold text-emerald-800':
                      question.answerKey &&
                      opt.trim().toLowerCase() === question.answerKey.trim().toLowerCase() &&
                      opt.trim().toLowerCase() !== getStudentAnswer(question).trim().toLowerCase(),
                    // Opsi biasa yang tidak dipilih dan bukan kunci
                    'border-slate-200 text-[#444444]':
                      opt.trim().toLowerCase() !== getStudentAnswer(question).trim().toLowerCase() &&
                      (!question.answerKey || opt.trim().toLowerCase() !== question.answerKey.trim().toLowerCase()),
                  }"
                >
                  <!-- Lingkaran indikator: biru=dipilih+benar, merah=dipilih+salah, abu=tidak dipilih -->
                  <span
                    class="size-4 shrink-0 rounded-full border-2 transition"
                    :class="{
                      'border-blue-500 bg-blue-500':
                        opt.trim().toLowerCase() === getStudentAnswer(question).trim().toLowerCase() &&
                        isAnswerCorrect(question) === true,
                      'border-red-500 bg-red-500':
                        opt.trim().toLowerCase() === getStudentAnswer(question).trim().toLowerCase() &&
                        isAnswerCorrect(question) === false,
                      'border-emerald-500 bg-emerald-100':
                        question.answerKey &&
                        opt.trim().toLowerCase() === question.answerKey.trim().toLowerCase() &&
                        opt.trim().toLowerCase() !== getStudentAnswer(question).trim().toLowerCase(),
                      'border-slate-300':
                        opt.trim().toLowerCase() !== getStudentAnswer(question).trim().toLowerCase() &&
                        (!question.answerKey || opt.trim().toLowerCase() !== question.answerKey.trim().toLowerCase()),
                    }"
                  />
                  <span class="flex-1">{{ opt }}</span>
                  <!-- Label kanan -->
                  <span
                    v-if="opt.trim().toLowerCase() === getStudentAnswer(question).trim().toLowerCase()"
                    class="shrink-0 text-xs font-bold"
                    :class="isAnswerCorrect(question) ? 'text-blue-600' : 'text-red-600'"
                  >
                    {{ isAnswerCorrect(question) ? '✓ Dipilih (Benar)' : '✗ Dipilih (Salah)' }}
                  </span>
                  <span
                    v-else-if="question.answerKey && opt.trim().toLowerCase() === question.answerKey.trim().toLowerCase()"
                    class="shrink-0 text-xs font-semibold text-emerald-700"
                  >
                    ✓ Kunci
                  </span>
                </div>
              </div>

              <!-- Jawaban Mahasiswa (esai / jawaban singkat saja — PG sudah terlihat di opsi) -->
              <div v-if="question.type !== 'multiple_choice'" class="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p class="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#888888]">
                  Jawaban Mahasiswa
                </p>
                <p class="text-sm font-medium text-[#333333] sm:text-base">
                  {{ getStudentAnswer(question) }}
                </p>
                <!-- Kunci esai -->
                <div
                  v-if="question.answerKey"
                  class="mt-3 border-t border-slate-200 pt-3"
                >
                  <p class="text-[10px] font-bold uppercase tracking-widest text-[#888888]">Kunci Jawaban</p>
                  <p class="mt-0.5 text-xs text-emerald-700">{{ question.answerKey }}</p>
                </div>
              </div>

              <!-- Input Nilai Dosen -->
              <div class="flex items-center justify-between gap-4 border-t border-slate-100 pt-4">
                <div>
                  <p class="text-sm font-semibold text-[#555555]">Nilai Soal Ini</p>
                  <p class="text-xs text-[#999999]">
                    Rentang: 0 – {{ question.points }}
                    <span
                      v-if="question.type === 'multiple_choice' && isAnswerCorrect(question) !== null"
                      class="ml-1 font-medium"
                      :class="isAnswerCorrect(question) ? 'text-blue-600' : 'text-red-500'"
                    >
                      · {{ isAnswerCorrect(question) ? 'Auto: nilai penuh' : 'Auto: 0' }} (bisa diubah)
                    </span>
                  </p>
                </div>
                <div class="flex items-center gap-2">
                  <input
                    v-if="!isDone && !submission.graded"
                    type="number"
                    min="0"
                    :max="question.points"
                    class="w-24 rounded-xl border border-slate-200 px-3 py-2 text-center text-sm font-bold outline-none transition focus:border-[#2864E8] focus:ring-2 focus:ring-[#2864E8]/20"
                    :value="scoreDrafts[question.id] ?? ''"
                    @input="scoreDrafts[question.id] = $event.target.value"
                  />
                  <span
                    v-else
                    class="min-w-[4rem] rounded-xl bg-[#2864E8]/10 px-4 py-2 text-center text-sm font-bold text-[#2864E8]"
                  >
                    {{
                      submission.answers?.find((a) => a.questionId === question.id)?.score ??
                      scoreDrafts[question.id] ??
                      '-'
                    }}
                  </span>
                  <span class="text-xs font-medium text-[#aaaaaa]">/ {{ question.points }}</span>
                </div>
              </div>
            </section>
          </TransitionGroup>

          <!-- Footer Kirim Nilai (sebelum dinilai) -->
          <section
            v-if="!isDone && !submission.graded"
            class="sticky bottom-4 z-10 rounded-[1.5rem] border border-[#e3e3e3] bg-white/95 p-4 shadow-xl backdrop-blur-sm sm:rounded-[2rem] sm:p-5"
          >
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p class="text-xs text-[#888888]">Total nilai yang akan dikirim</p>
                <p class="text-2xl font-bold leading-none text-[#2864E8]">
                  {{ totalInput }}
                  <span class="text-base font-normal text-[#aaaaaa]">/ {{ maxScore }}</span>
                </p>
              </div>
              <button
                type="button"
                :disabled="isSubmitting"
                class="motion-control cursor-pointer rounded-xl bg-[#2864E8] px-8 py-3 text-sm font-bold text-white shadow-md transition hover:bg-[#1f50be] active:scale-95 disabled:opacity-50 sm:px-10 sm:text-base"
                @click="submitGrade"
              >
                {{ isSubmitting ? 'Mengirim...' : 'Kirim Nilai' }}
              </button>
            </div>
          </section>

          <!-- State sudah dinilai -->
          <section
            v-else-if="isDone || submission.graded"
            class="rounded-[1.5rem] border border-emerald-200 bg-emerald-50 p-6 text-center shadow-sm sm:rounded-[2rem] sm:p-8"
          >
            <div
              class="mx-auto flex size-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-600"
            >
              <svg class="size-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="m5 12 4 4L19 6" />
              </svg>
            </div>
            <h3 class="mt-3 text-lg font-bold text-emerald-800">Nilai Berhasil Dikirim!</h3>
            <p class="mt-1 text-sm text-emerald-700">
              Nilai <strong>{{ isDone ? totalInput : submission.score }}</strong> / {{ maxScore }}
              telah dikirim ke <strong>{{ submission.name || submission.email }}</strong>.
            </p>
            <button
              type="button"
              class="mt-5 cursor-pointer rounded-xl bg-[#2864E8] px-7 py-2.5 text-sm font-semibold text-white shadow transition hover:bg-[#1f50be]"
              @click="router.push(`/kelas/${classId}/tugas/${taskId}`)"
            >
              Kembali ke Hasil Kuis
            </button>
          </section>
        </template>
      </div>
    </div>
  </DashboardLayout>
</template>

<style scoped>
.question-card-enter-active,
.question-card-leave-active,
.question-card-move {
  transition:
    opacity 0.35s ease,
    transform 0.35s cubic-bezier(0.2, 0.7, 0.2, 1);
}
.question-card-enter-from,
.question-card-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.985);
}
.question-card-leave-active {
  position: absolute;
  width: 100%;
}
@media (prefers-reduced-motion: reduce) {
  .question-card-enter-active,
  .question-card-leave-active,
  .question-card-move {
    transition: none;
  }
}
</style>
