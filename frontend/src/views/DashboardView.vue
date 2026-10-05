<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import {
  addClass,
  deleteClass,
  leaveClass,
  getClassesForStudent,
  getClassesForTeacher,
  joinClassByCode,
} from '@/composables/useClasses.js'
import DashboardLayout from '@/layouts/DashboardLayout.vue'
import ClassCard from '@/components/dashboard/ClassCard.vue'
import CreateClassModal from '@/components/dashboard/CreateClassModal.vue'
import JoinClassModal from '@/components/dashboard/JoinClassModal.vue'
import bannerImg from '@/assets/images/dashboard-banner.png'
import { canStudentViewTask } from '@/utils/scannedTaskAccess.js'

const router = useRouter()
const { user } = useAuth()
const isStudent = computed(() => user.value?.role === 'student')

const classList = computed(() => {
  if (isStudent.value) {
    return getClassesForStudent(user.value?.email, user.value?.id)
  }
  return getClassesForTeacher(user.value?.email, user.value?.id, user.value?.name)
})

const upcomingQuizzes = computed(() => {
  if (!isStudent.value) return []

  const now = Date.now()
  return classList.value
    .flatMap((classItem) =>
      (classItem.tasks || [])
        .filter((task) => canStudentViewTask(task, user.value?.id, user.value?.email))
        .map((task) => {
          const dueAt =
            task.dueAt ||
            (task.deadlineDate
              ? `${task.deadlineDate}T${task.deadlineTime || '23:59'}:00+08:00`
              : '')
          return { classItem, task, dueAt, dueTimestamp: dueAt ? new Date(dueAt).getTime() : 0 }
        }),
    )
    .filter(({ task, dueTimestamp }) => {
      if (!dueTimestamp || dueTimestamp < now) return false
      const email = user.value?.email?.trim().toLowerCase()
      return !task.submissions?.some(
        (submission) => submission.email?.trim().toLowerCase() === email,
      )
    })
    .sort((first, second) => first.dueTimestamp - second.dueTimestamp)
})
const isCreateModalOpen = ref(false)
const isJoinModalOpen = ref(false)
const joinMessage = ref('')
const joinMessageIsError = ref(true)

const confirmModal = ref({
  isOpen: false,
  type: '', // 'delete' | 'leave'
  classItem: null,
})

function confirmDeleteClass(classItem) {
  confirmModal.value = {
    isOpen: true,
    type: 'delete',
    classItem,
  }
}

function confirmLeaveClass(classItem) {
  confirmModal.value = {
    isOpen: true,
    type: 'leave',
    classItem,
  }
}

async function handleConfirmAction() {
  const { type, classItem } = confirmModal.value
  if (!classItem) return

  if (type === 'delete') {
    await deleteClass(classItem.id)
  } else if (type === 'leave') {
    await leaveClass(user.value?.email, classItem.id)
  }

  confirmModal.value.isOpen = false
}

function openCreateModal() {
  isCreateModalOpen.value = true
}

function openJoinModal() {
  joinMessage.value = ''
  isJoinModalOpen.value = true
}

async function handleCreateClass(newClass) {
  await addClass(newClass)
}

async function handleJoinClass(code) {
  const result = await joinClassByCode(user.value?.email || '', code)

  if (result.status === 'not-found') {
    joinMessage.value = 'Kode kelas tidak ditemukan. Periksa kembali kode dari dosen.'
    joinMessageIsError.value = true
    return
  }

  if (result.status === 'already-joined') {
    joinMessage.value = 'Kamu sudah tergabung di kelas ini.'
    joinMessageIsError.value = true
    return
  }

  if (result.status === 'storage-error') {
    joinMessage.value = 'Kelas belum bisa disimpan di perangkat ini.'
    joinMessageIsError.value = true
    return
  }

  joinMessage.value = ''
  isJoinModalOpen.value = false
}

function handleClassClick(classItem) {
  router.push(`/kelas/${classItem.id}`)
}

function handleUpcomingQuizClick(reminder) {
  router.push(`/kelas/${reminder.classItem.id}/tugas/${reminder.task.id}`)
}

function formatDeadline(timestamp) {
  return new Date(timestamp).toLocaleDateString('id-ID', {
    weekday: 'long',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}
</script>

<template>
  <DashboardLayout>
    <div class="space-y-4 sm:space-y-[22px]">
      <!-- Banner Gambar Selamat Datang -->
      <section
        class="overflow-hidden rounded-[1.5rem] border-4 border-white sm:rounded-[2rem] bg-[#0e66f5] shadow-sm"
      >
        <img
          :src="bannerImg"
          alt="Selamat Datang di KeyQuiz - Esai Tepat, Nilai Cepat, Evaluasi Hemat Waktu Tanpa Subjetivitas"
          class="block h-auto w-full select-none"
        />
      </section>

      <section
        v-if="isStudent"
        class="rounded-[1rem] bg-white p-4 sm:rounded-2xl sm:p-5"
        aria-label="Kuis yang segera tenggat"
      >
        <h2 class="border-b border-[#d6d6d6] pb-2 text-base font-medium text-[#808080] sm:text-xl">
          Harus Dikerjakan Segera
        </h2>
        <button
          v-for="reminder in upcomingQuizzes"
          :key="`${reminder.classItem.id}-${reminder.task.id}`"
          type="button"
          class="motion-control mt-2 flex w-full flex-wrap items-center justify-between gap-2 rounded-xl border border-[#888888] px-4 py-3 text-left transition hover:border-[#2864E8] hover:bg-blue-50/30"
          @click="handleUpcomingQuizClick(reminder)"
        >
          <span class="text-sm font-medium text-[#222222] sm:text-base">
            {{ reminder.task.title }} : {{ reminder.classItem.title }}
          </span>
          <span class="text-xs text-[#777777] sm:text-sm">
            {{ formatDeadline(reminder.dueTimestamp) }}
          </span>
        </button>
        <p v-if="upcomingQuizzes.length === 0" class="pt-3 text-sm text-[#777777]">
          Tidak ada kuis dengan tenggat mendatang.
        </p>
      </section>

      <!-- Kelas -->
      <section class="rounded-[1.5rem] bg-white p-3.5 sm:rounded-[2rem] sm:p-7 lg:p-[35px]">
        <div class="mb-4 flex items-center justify-between sm:mb-5">
          <h2 class="text-lg font-normal text-[#777777] sm:text-[22px]">Kelas</h2>
          <button
            type="button"
            class="motion-control cursor-pointer text-base font-medium text-[#2864E8] transition hover:underline sm:text-[22px]"
            @click="isStudent ? openJoinModal() : openCreateModal()"
          >
            + Tambah Kelas
          </button>
        </div>

        <div
          v-if="classList.length > 0"
          class="motion-stagger grid grid-cols-2 gap-2.5 sm:gap-3 lg:grid-cols-3 lg:gap-[13px]"
        >
          <ClassCard
            v-for="c in classList"
            :key="c.id"
            :title="c.title"
            :major="c.major"
            :lecturer="c.lecturer"
            :code="isStudent ? '' : c.code"
            :is-student="isStudent"
            @click="handleClassClick(c)"
            @delete="confirmDeleteClass(c)"
            @leave="confirmLeaveClass(c)"
          />
        </div>
        
        <!-- Empty State jika belum ada kelas -->
        <div
          v-else
          class="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 py-12 px-4 text-center sm:py-16"
        >
          <div class="mb-3 flex size-12 items-center justify-center rounded-full bg-blue-50 text-[#2864E8]">
            <svg class="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <p class="text-base font-medium text-[#777777] sm:text-lg">
            <template v-if="isStudent">
              belum masuk kelas manapun
            </template>
            <template v-else>
              Belum ada kelas yang dibuat
            </template>
          </p>
          <p v-if="isStudent" class="mt-1.5 text-xs text-[#999999] sm:text-sm">
            Klik tombol <strong>+ Tambah Kelas</strong> di atas dan masukkan kode kelas untuk bergabung.
          </p>
          <p v-else class="mt-1.5 text-xs text-[#999999] sm:text-sm">
            Klik tombol <strong>+ Tambah Kelas</strong> di atas untuk membuat kelas baru.
          </p>
        </div>

        <p
          v-if="isStudent && joinMessage && !isJoinModalOpen"
          class="mt-3 text-sm text-red-600"
          role="status"
        >
          {{ joinMessage }}
        </p>
      </section>
    </div>

    <!-- Modal Buat Kelas (Dosen) -->
    <CreateClassModal v-model:open="isCreateModalOpen" @create="handleCreateClass" />
    
    <!-- Modal Tambah / Gabung Kelas (Mahasiswa) -->
    <JoinClassModal
      v-model:open="isJoinModalOpen"
      :message="joinMessage"
      :is-error="joinMessageIsError"
      @join="handleJoinClass"
    />

    <!-- Modal Konfirmasi Hapus / Keluar Kelas -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div
          v-if="confirmModal.isOpen"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-xs"
          role="dialog"
          aria-modal="true"
          @click.self="confirmModal.isOpen = false"
        >
          <div
            class="w-full max-w-[420px] overflow-hidden rounded-[20px] bg-white shadow-2xl transition-all animate-scale-up"
          >
            <div class="relative flex items-center justify-center bg-red-600 px-6 py-4">
              <h2 class="text-lg font-bold text-white tracking-wide sm:text-xl">
                {{ confirmModal.type === 'delete' ? 'Hapus Kelas' : 'Keluar dari Kelas' }}
              </h2>
            </div>
            <div class="p-6 text-center">
              <p class="text-sm text-gray-700 sm:text-base leading-relaxed">
                <template v-if="confirmModal.type === 'delete'">
                  Apakah Anda yakin ingin menghapus kelas <strong>{{ confirmModal.classItem?.title }}</strong>? Seluruh data tugas dan kuis di kelas ini akan dihapus.
                </template>
                <template v-else>
                  Apakah Anda yakin ingin keluar dari kelas <strong>{{ confirmModal.classItem?.title }}</strong>?
                </template>
              </p>
              <div class="mt-6 flex justify-center gap-3">
                <button
                  type="button"
                  class="cursor-pointer rounded-xl border border-gray-300 px-5 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition active:scale-95"
                  @click="confirmModal.isOpen = false"
                >
                  Batal
                </button>
                <button
                  type="button"
                  class="cursor-pointer rounded-xl bg-red-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-red-700 transition active:scale-95"
                  @click="handleConfirmAction"
                >
                  {{ confirmModal.type === 'delete' ? 'Hapus' : 'Keluar' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
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
