<script setup>
import { ref, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DashboardLayout from '@/layouts/DashboardLayout.vue'
import aiBannerImg from '@/assets/images/bennerbuatsoal_ai.png'
import sendFillIcon from '@/assets/icons/Send_fill.svg'
import { classes } from '@/composables/useClasses.js'
import { generateQuizAI } from '@/services/api.js'
import { resolveMultipleChoiceAnswerKey } from '@/utils/quizAnswerKey.js'

const route = useRoute()
const router = useRouter()

const classId = computed(() => route.params.id || 1)
const currentClass = computed(() => {
  return classes.value.find((c) => String(c.id) === String(classId.value)) || classes.value[0]
})

const inputPrompt = ref('')
const isSubmitted = ref(false)
const suggestedTaskTitle = ref('')
const conversationMessages = ref([])
const latestQuizMessageId = ref(null)
const chatScrollAreaRef = ref(null)
const fileInput = ref(null)
const attachedFiles = ref([])

const isGeneratingAi = ref(false)
const generatedQuestionsList = ref([])

function formatQuizResponse(quiz) {
  let formattedText = `Berikut soal yang berhasil dibuat untuk "${quiz.judul || 'kuis'}":\n\n`
  const esaiList = quiz.soal.filter((question) => question.tipe === 'essay')
  const pgList = quiz.soal.filter((question) => question.tipe === 'multiple_choice')

  if (esaiList.length > 0) {
    formattedText += 'Soal Esai:\n'
    esaiList.forEach((question, index) => {
      formattedText += `${index + 1}. ${question.pertanyaan}\n`
      if (question.kunci_jawaban) formattedText += `   Kunci: ${question.kunci_jawaban}\n`
    })
    formattedText += '\n'
  }

  if (pgList.length > 0) {
    formattedText += 'Soal Pilihan Ganda:\n'
    pgList.forEach((question, index) => {
      const nomor = esaiList.length + index + 1
      formattedText += `${nomor}. ${question.pertanyaan}\n`
      question.opsi?.forEach((option) => {
        formattedText += `${option.huruf}. ${option.teks}\n`
      })
      formattedText += `Jawaban: ${question.kunci_jawaban}\n\n`
    })
  }

  return formattedText.trim()
}

function openFilePicker() {
  fileInput.value?.click()
}

function handleFileSelection(event) {
  const files = Array.from(event.target.files || [])
  attachedFiles.value = [...attachedFiles.value, ...files]
  event.target.value = ''
}

function removeAttachedFile(index) {
  attachedFiles.value.splice(index, 1)
}

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function handleSubmitPrompt() {
  if (isGeneratingAi.value) return

  const prompt = inputPrompt.value.trim()
  if (!prompt && attachedFiles.value.length === 0) return

  const userMessage = prompt || 'Tolong analisis dokumen ini.'
  const history = conversationMessages.value
    .filter((message) => typeof message.content === 'string' && message.content.trim())
    .map(({ role, content }) => ({ role, content }))
  const userAttachments = attachedFiles.value.map(({ name, size }) => ({ name, size }))
  attachedFiles.value = []
  isSubmitted.value = true
  inputPrompt.value = ''
  isGeneratingAi.value = true

  conversationMessages.value.push({
    id: `user-${Date.now()}`,
    role: 'user',
    content: userMessage,
    displayContent: userMessage,
    attachments: userAttachments,
  })
  const assistantMessage = {
    id: `assistant-${Date.now()}`,
    role: 'assistant',
    content: null,
    displayContent: '',
    isGenerating: true,
  }
  conversationMessages.value.push(assistantMessage)
  nextTick(() => {
    if (chatScrollAreaRef.value) {
      chatScrollAreaRef.value.scrollTop = chatScrollAreaRef.value.scrollHeight
    }
  })

  try {
    const aiData = await generateQuizAI({
      prompt: userMessage,
      history,
      jumlahPg: 3,
      jumlahEsai: 2,
    })
    if (!Array.isArray(aiData?.soal)) {
      throw new Error('AI tidak mengembalikan struktur soal yang valid.')
    }

    suggestedTaskTitle.value = aiData.judul || userMessage
    assistantMessage.content = JSON.stringify(aiData)
    assistantMessage.displayContent = formatQuizResponse(aiData)
    assistantMessage.isGenerating = false
    latestQuizMessageId.value = assistantMessage.id
    generatedQuestionsList.value = aiData.soal.map((question, index) => ({
      id: Date.now() + index,
      title: question.pertanyaan,
      type: question.tipe === 'multiple_choice' ? 'multiple_choice' : 'short_answer',
      options: question.opsi ? question.opsi.map((option) => option.teks) : [],
      answerKey:
        question.tipe === 'multiple_choice'
          ? resolveMultipleChoiceAnswerKey(question.opsi, question.kunci_jawaban)
          : question.kunci_jawaban || '',
      rubric: question.rubrik || [],
      points: question.bobot || 10,
    }))
  } catch (err) {
    console.error('[AI Quiz]', err)
    assistantMessage.content = null
    assistantMessage.displayContent = `Gagal membuat soal: ${err.message}`
    assistantMessage.isError = true
    assistantMessage.isGenerating = false
  } finally {
    isGeneratingAi.value = false
    nextTick(() => {
      if (chatScrollAreaRef.value) {
        chatScrollAreaRef.value.scrollTop = chatScrollAreaRef.value.scrollHeight
      }
    })
  }
}

function handleKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSubmitPrompt()
  }
}

function handleAgree() {
  router.push({
    name: 'create-quiz-manual',
    params: { id: classId.value },
    state: {
      aiTitle: suggestedTaskTitle.value || 'Kuis AI',
      aiQuestions: JSON.stringify(generatedQuestionsList.value),
    },
  })
}
</script>

<template>
  <!-- Gunakan :no-scroll="true" agar border/latar biru tetap terkunci dan tidak ikut bergeser -->
  <DashboardLayout :no-scroll="true">
    <input
      ref="fileInput"
      type="file"
      multiple
      accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.csv,image/*"
      class="hidden"
      @change="handleFileSelection"
    />
    <div class="flex flex-col flex-1 h-full min-h-0">
      <!-- Breadcrumb Navigasi Kembali: Tetap berada di atas / Statis tidak ikut scroll -->
      <div class="flex items-center justify-between pb-3 sm:pb-3.5 text-white/90 shrink-0">
        <button
          type="button"
          class="flex cursor-pointer items-center gap-1.5 text-xs font-semibold text-white/90 transition hover:text-white hover:translate-x-[-2px] sm:text-sm"
          @click="router.push(`/kelas/${classId}`)"
        >
          <svg class="size-4 sm:size-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2.5"
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Kembali ke Kelas
        </button>

        <span
          class="text-xs text-white/80 sm:text-sm font-medium truncate max-w-[200px] sm:max-w-md"
        >
          {{ currentClass.title }}
        </span>
      </div>

      <!-- TAMPILAN 1: SEBELUM USER INPUT PERINTAH (Sesuai Foto 1) -->
      <div
        v-if="!isSubmitted"
        class="flex-1 flex flex-col min-h-0 space-y-3 sm:space-y-4 overflow-y-auto pr-0.5"
      >
        <!-- Banner Manfaatkan AI Untuk Membuat Soal -->
        <section
          class="overflow-hidden rounded-[1.5rem] border-4 border-white bg-white shadow-sm sm:rounded-[2rem] shrink-0"
        >
          <img
            :src="aiBannerImg"
            alt="Manfaatkan AI Untuk Membuat Soal"
            class="block h-auto w-full select-none object-cover"
          />
        </section>

        <!-- Kotak Putih Tempat Chat / Prompt Awal -->
        <section
          class="flex-1 flex flex-col items-center justify-center rounded-[1.5rem] border border-white/80 bg-[linear-gradient(180deg,#2563EB_0%,#808080_100%)] p-6 shadow-sm sm:rounded-[2rem] sm:p-12 min-h-[300px]"
        >
          <div class="w-full max-w-2xl text-center">
            <!-- Teks Tengah: Ada ide baru untuk hari ini? -->
            <h1 class="text-2xl font-bold text-white sm:text-3xl lg:text-4xl tracking-tight">
              Ada ide baru untuk hari ini?
            </h1>

            <!-- Input Bar Melengkung Pill -->
            <div class="mt-8 sm:mt-12 w-full">
              <div v-if="attachedFiles.length" class="mb-3 flex flex-wrap gap-2 text-left">
                <div
                  v-for="(file, index) in attachedFiles"
                  :key="`${file.name}-${file.size}-${index}`"
                  class="flex max-w-full items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-[#444444]"
                >
                  <span class="truncate">{{ file.name }}</span>
                  <span class="shrink-0 text-[#888888]">{{ formatFileSize(file.size) }}</span>
                  <button
                    type="button"
                    class="shrink-0 text-[#888888] hover:text-red-600"
                    :aria-label="`Hapus lampiran ${file.name}`"
                    @click="removeAttachedFile(index)"
                  >
                    &times;
                  </button>
                </div>
              </div>
              <div
                class="flex items-center rounded-full border-2 border-[#2864E8] bg-white px-4 py-2 sm:px-6 sm:py-3 shadow-sm transition-all focus-within:shadow-md"
              >
                <!-- Tombol Plus Kiri -->
                <button
                  type="button"
                  class="flex items-center gap-2 cursor-pointer text-[#2864E8] transition hover:opacity-80 shrink-0"
                  @click="openFilePicker"
                  aria-label="Lampirkan dokumen"
                  title="Lampirkan dokumen"
                >
                  <svg
                    class="size-6 sm:size-7"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2.5"
                      d="M12 4v16m8-8H4"
                    />
                  </svg>
                </button>

                <!-- Input Text -->
                <input
                  v-model="inputPrompt"
                  type="text"
                  placeholder="Mulai berdiskusi"
                  class="w-full bg-transparent px-3 text-sm text-[#444444] placeholder-[#888888] outline-none sm:px-4 sm:text-base lg:text-lg"
                  @keydown="handleKeyDown"
                />

                <!-- Tombol Kirim Kanan (Icon Send Fill) -->
                <button
                  type="button"
                  class="motion-control cursor-pointer shrink-0 transition hover:scale-105 active:scale-95 text-[#2864E8] p-1"
                  aria-label="Kirim Perintah"
                  @click="handleSubmitPrompt"
                >
                  <img :src="sendFillIcon" alt="Kirim" class="size-6 sm:size-7" />
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- TAMPILAN 2: SETELAH USER INPUT PERINTAH (Sesuai Foto 2) -->
      <!-- Menggunakan layout Flex Col di mana container pesan bisa di-scroll, dan input bar POSISINYA TETAP di bawah -->
      <div
        v-else
        class="flex-1 flex flex-col min-h-0 overflow-hidden rounded-[1.5rem] border border-white/80 border-b-0 bg-[linear-gradient(180deg,#2563EB_0%,#808080_100%)] p-4 pb-8 shadow-sm sm:rounded-[2rem] sm:p-7 sm:pb-10 lg:p-9 lg:pb-14"
      >
        <!-- Area Percakapan Bubble Chat (Scrollable mandiri di dalam kotak putih) -->
        <div
          ref="chatScrollAreaRef"
          class="flex-1 min-h-0 overflow-y-auto space-y-6 px-2 py-2 pr-3 sm:px-3 sm:py-3 sm:pr-4"
        >
          <template v-for="message in conversationMessages" :key="message.id">
            <div v-if="message.role === 'user'" class="flex justify-end pt-2">
            <div class="relative max-w-[85%] sm:max-w-2xl">
              <!-- Kotak Balon User: Border biru melengkung, sudut kanan bawah menjadi pangkal ekor -->
              <div
                class="rounded-[24px] rounded-br-[4px] border-2 border-[#2864E8] bg-white px-5 py-3.5 sm:px-6 sm:py-4 text-sm sm:text-base font-medium text-[#222222] shadow-sm leading-relaxed"
              >
                {{ message.displayContent }}
                <div v-if="message.attachments.length" class="mt-3 flex flex-wrap gap-2">
                  <span
                    v-for="(file, index) in message.attachments"
                    :key="`${file.name}-${file.size}-${index}`"
                    class="max-w-full truncate rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-normal text-[#555555]"
                  >
                    {{ file.name }} · {{ formatFileSize(file.size) }}
                  </span>
                </div>
              </div>

              <!-- Ekor SVG Balon Chat User Sesuai Foto 2 (Kanan Bawah) -->
              <svg
                class="absolute -bottom-[9px] -right-[1px] w-[18px] h-[12px] pointer-events-none"
                viewBox="0 0 18 12"
                fill="none"
              >
                <!-- Isi Putih Balon -->
                <path d="M0 0C6 1 12 5 18 12C14 6 10 2 0 0Z" fill="white" />
                <!-- Border Garis Biru -->
                <path
                  d="M0 0C6 1 12 5 18 12"
                  stroke="#2864E8"
                  stroke-width="2"
                  stroke-linecap="round"
                />
              </svg>
            </div>
            </div>

            <div v-else class="flex justify-start">
            <div class="relative max-w-[96%] sm:max-w-3xl w-full">
              <!-- Kotak Balon AI: Border biru melengkung, sudut kiri bawah menjadi pangkal ekor -->
              <div
                class="rounded-[28px] rounded-bl-[4px] border-2 border-[#2864E8] bg-white p-5 sm:p-8 text-xs sm:text-sm lg:text-[15px] font-normal text-[#222222] shadow-sm leading-relaxed whitespace-pre-line"
                :class="{ 'text-red-700': message.isError }"
              >
                <div v-if="message.isGenerating" class="flex items-center gap-3 text-slate-500 font-medium py-2">
                  <svg class="animate-spin size-5 text-[#2864E8]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Sedang memproses dan menyusun soal dengan AI...</span>
                </div>
                <div v-else>
                  {{ message.displayContent }}
                </div>
              </div>

              <!-- Ekor SVG Balon Chat AI Sesuai Foto 2 (Kiri Bawah) -->
              <svg
                class="absolute -bottom-[9px] -left-[1px] w-[18px] h-[12px] pointer-events-none"
                viewBox="0 0 18 12"
                fill="none"
              >
                <!-- Isi Putih Balon -->
                <path d="M18 0C12 1 6 5 0 12C4 6 8 2 18 0Z" fill="white" />
                <!-- Border Garis Biru -->
                <path
                  d="M18 0C12 1 6 5 0 12"
                  stroke="#2864E8"
                  stroke-width="2"
                  stroke-linecap="round"
                />
              </svg>
              <div v-if="message.id === latestQuizMessageId" class="mt-3 flex justify-end">
                <button
                  type="button"
                  class="motion-control cursor-pointer rounded-xl bg-[#2864E8] px-8 py-2.5 text-sm font-semibold text-white shadow-md transition duration-200 hover:bg-[#1f50be] hover:shadow-lg active:scale-95 disabled:cursor-not-allowed disabled:opacity-60 sm:px-10 sm:py-3 sm:text-base"
                  :disabled="isGeneratingAi"
                  @click="handleAgree"
                >
                  Setuju
                </button>
              </div>
            </div>
            </div>
          </template>
        </div>

        <!-- Tombol / Bar Ketik Perintah (Posisi Tetap / Pinned di Bagian Bawah Kotak) -->
        <div class="shrink-0 pt-3 sm:pt-4 border-t border-slate-100 mt-2">
          <div v-if="attachedFiles.length" class="mb-3 flex flex-wrap gap-2">
            <div
              v-for="(file, index) in attachedFiles"
              :key="`${file.name}-${file.size}-${index}`"
              class="flex max-w-full items-center gap-2 rounded-xl border border-white/60 bg-white/90 px-3 py-2 text-xs text-[#444444]"
            >
              <span class="truncate">{{ file.name }}</span>
              <span class="shrink-0 text-[#888888]">{{ formatFileSize(file.size) }}</span>
              <button
                type="button"
                class="shrink-0 text-[#888888] hover:text-red-600"
                :aria-label="`Hapus lampiran ${file.name}`"
                @click="removeAttachedFile(index)"
              >
                &times;
              </button>
            </div>
          </div>
          <div
            class="flex items-center rounded-full border-2 border-[#2864E8] bg-white px-4 py-2 sm:px-6 sm:py-3 shadow-sm transition-all focus-within:shadow-md"
          >
            <!-- Tombol Plus Kiri -->
            <button
              type="button"
              class="flex items-center gap-2 cursor-pointer text-[#2864E8] transition hover:opacity-80 shrink-0"
              @click="openFilePicker"
              aria-label="Lampirkan dokumen"
              title="Lampirkan dokumen"
            >
              <svg class="size-6 sm:size-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2.5"
                  d="M12 4v16m8-8H4"
                />
              </svg>
            </button>

            <!-- Input Text -->
            <input
              v-model="inputPrompt"
              type="text"
              placeholder="Mulai berdiskusi"
              class="w-full bg-transparent px-3 text-sm text-[#444444] placeholder-[#888888] outline-none sm:px-4 sm:text-base lg:text-lg"
              :disabled="isGeneratingAi"
              @keydown="handleKeyDown"
            />

            <!-- Tombol Kirim Kanan -->
            <button
              type="button"
              class="cursor-pointer shrink-0 transition hover:scale-105 active:scale-95 text-[#2864E8] p-1 disabled:cursor-not-allowed disabled:opacity-60"
              aria-label="Kirim Perintah"
              :disabled="isGeneratingAi"
              @click="handleSubmitPrompt"
            >
              <img :src="sendFillIcon" alt="Kirim" class="size-6 sm:size-7" />
            </button>
          </div>
        </div>
      </div>
    </div>
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
</style>
