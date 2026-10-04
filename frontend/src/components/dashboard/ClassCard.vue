<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  major: { type: String, required: true },
  lecturer: { type: String, required: true },
  code: { type: String, default: '' },
  isStudent: { type: Boolean, default: false },
})

const emit = defineEmits(['delete', 'leave'])

const isMenuOpen = ref(false)
const copied = ref(false)

function handleCopyCode() {
  if (!props.code) return
  navigator.clipboard.writeText(props.code).then(() => {
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  })
}

function toggleMenu() {
  isMenuOpen.value = !isMenuOpen.value
}

function closeMenu() {
  isMenuOpen.value = false
}

function handleDelete() {
  closeMenu()
  emit('delete')
}

function handleLeave() {
  closeMenu()
  emit('leave')
}

function onKeydown(e) {
  if (e.key === 'Escape' && isMenuOpen.value) {
    closeMenu()
  }
}

onMounted(() => {
  window.addEventListener('click', closeMenu)
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', closeMenu)
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <article
    class="motion-surface relative flex min-h-[150px] cursor-pointer flex-col rounded-lg border border-[#888888] bg-white p-3 shadow-[3px_3px_4px_rgba(0,0,0,0.25)] transition hover:-translate-y-0.5 hover:shadow-[4px_5px_8px_rgba(0,0,0,0.3)] sm:min-h-[200px] sm:p-5 lg:min-h-[255px] lg:p-6"
  >
    <!-- Header: Judul & Titik Tiga -->
    <div class="flex items-start justify-between gap-2">
      <div class="min-w-0 flex-1">
        <h3 class="text-sm font-medium leading-snug text-black sm:text-xl lg:text-2xl">{{ title }}</h3>
        <p class="mt-1 text-xs text-[#808080] sm:text-sm lg:text-[15px]">{{ major }}</p>
      </div>

      <!-- Tombol Titik Tiga -->
      <div class="relative shrink-0" @click.stop>
        <button
          type="button"
          class="flex size-7 items-center justify-center rounded-full text-[#777777] transition hover:bg-black/5 hover:text-black focus:outline-none sm:size-8"
          title="Opsi kelas"
          aria-label="Opsi kelas"
          @click="toggleMenu"
        >
          <svg class="size-5" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="5" r="1.75" />
            <circle cx="12" cy="12" r="1.75" />
            <circle cx="12" cy="19" r="1.75" />
          </svg>
        </button>

        <!-- Menu Dropdown -->
        <Transition name="dropdown-scale">
          <div
            v-if="isMenuOpen"
            class="absolute right-0 top-full z-30 mt-1 min-w-[150px] overflow-hidden rounded-xl border border-slate-200 bg-white py-1 shadow-lg ring-1 ring-black/5"
          >
            <button
              v-if="!isStudent"
              type="button"
              class="flex w-full items-center gap-2 px-3.5 py-2 text-left text-xs font-medium text-red-600 transition hover:bg-red-50 sm:text-sm"
              @click="handleDelete"
            >
              <svg class="size-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
              <span>Hapus Kelas</span>
            </button>

            <button
              v-else
              type="button"
              class="flex w-full items-center gap-2 px-3.5 py-2 text-left text-xs font-medium text-red-600 transition hover:bg-red-50 sm:text-sm"
              @click="handleLeave"
            >
              <svg class="size-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                />
              </svg>
              <span>Keluar dari Kelas</span>
            </button>
          </div>
        </Transition>
      </div>
    </div>

    <div
      v-if="code"
      class="mt-2.5 flex items-center justify-between gap-2 rounded-lg bg-blue-50/80 px-2.5 py-1.5 border border-blue-200/60"
      @click.stop
    >
      <div class="flex items-center gap-1.5 min-w-0">
        <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Kode:</span>
        <span class="font-mono text-xs font-bold tracking-wider text-[#2864E8] truncate">{{ code }}</span>
      </div>
      <button
        type="button"
        class="shrink-0 cursor-pointer rounded px-2 py-0.5 text-[11px] font-semibold text-[#2864E8] hover:bg-blue-100/70 active:scale-95 transition"
        :title="'Salin kode kelas ' + code"
        @click.stop="handleCopyCode"
      >
        {{ copied ? 'Tersalin!' : 'Salin' }}
      </button>
    </div>

    <div class="mt-auto flex items-center gap-2 pt-3 sm:gap-2.5 sm:pt-4">
      <!-- avatar placeholder -->
      <svg class="size-6 shrink-0 sm:size-[30px]" viewBox="0 0 30 30" aria-hidden="true">
        <circle cx="15" cy="15" r="15" fill="#D9D9D9" />
        <circle cx="15" cy="12" r="5" fill="#8a8a8a" />
        <path
          d="M5.5 25c1.2-4.2 5-6.5 9.5-6.5s8.3 2.3 9.5 6.5A15 15 0 0 1 15 30a15 15 0 0 1-9.5-5z"
          fill="#8a8a8a"
        />
      </svg>
      <span
        class="min-w-0 text-[11px] font-medium leading-tight text-[#666666] sm:text-sm lg:text-[15px]"
        >{{ lecturer }}</span
      >
    </div>
  </article>
</template>

<style scoped>
.dropdown-scale-enter-active,
.dropdown-scale-leave-active {
  transition: all 0.15s ease-out;
}

.dropdown-scale-enter-from,
.dropdown-scale-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
