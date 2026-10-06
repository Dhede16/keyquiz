<script setup>
import { computed, ref, watch } from 'vue'
import calendarIcon from '@/assets/icons/Date_range.svg'
import clockIcon from '@/assets/icons/Clock.svg'

const props = defineProps({
  open: { type: Boolean, default: false },
  showTitle: { type: Boolean, default: false },
  initialTitle: { type: String, default: '' },
})

const emit = defineEmits(['close', 'save'])
const taskTitle = ref('')
const deadlineDate = ref('')
const deadlineTime = ref('23:59')
const timeInput = ref(null)
const showDatePicker = ref(false)
const showTimePicker = ref(false)
const timeDraft = ref('23:59')
const visibleMonth = ref(new Date())

function formatDate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function parseDate(value) {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year, month - 1, day)
}

const minDate = computed(() => formatDate(new Date()))
const selectedDateLabel = computed(() =>
  deadlineDate.value
    ? new Intl.DateTimeFormat('id-ID', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      }).format(parseDate(deadlineDate.value))
    : 'Pilih tanggal',
)
const visibleMonthLabel = computed(() =>
  new Intl.DateTimeFormat('id-ID', { month: 'long', year: 'numeric' }).format(
    visibleMonth.value,
  ),
)
const calendarDays = computed(() => {
  const year = visibleMonth.value.getFullYear()
  const month = visibleMonth.value.getMonth()
  const firstDayOffset = (new Date(year, month, 1).getDay() + 6) % 7
  const firstDate = new Date(year, month, 1 - firstDayOffset)

  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(firstDate)
    date.setDate(firstDate.getDate() + index)
    return {
      date,
      value: formatDate(date),
      day: date.getDate(),
      inMonth: date.getMonth() === month,
    }
  })
})

watch(
  () => props.open,
  (isOpen) => {
    if (!isOpen) return

    taskTitle.value = props.initialTitle.slice(0, 120)
    const defaultDate = new Date()
    defaultDate.setDate(defaultDate.getDate() + 14)
    deadlineDate.value = formatDate(defaultDate)
    visibleMonth.value = new Date(defaultDate.getFullYear(), defaultDate.getMonth(), 1)
    deadlineTime.value = '23:59'
    timeDraft.value = '23:59'
    showDatePicker.value = false
    showTimePicker.value = false
  },
)

function changeMonth(offset) {
  visibleMonth.value = new Date(
    visibleMonth.value.getFullYear(),
    visibleMonth.value.getMonth() + offset,
    1,
  )
}

function selectDate(day) {
  if (day.value < minDate.value) return
  deadlineDate.value = day.value
  showDatePicker.value = false
}

function toggleDatePicker() {
  showDatePicker.value = !showDatePicker.value
  showTimePicker.value = false
  if (showDatePicker.value && deadlineDate.value) {
    const selectedDate = parseDate(deadlineDate.value)
    visibleMonth.value = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1)
  }
}

function toggleTimePicker() {
  showTimePicker.value = !showTimePicker.value
  showDatePicker.value = false
  timeDraft.value = deadlineTime.value
}

function openNativeTimePicker() {
  if (!timeInput.value) return
  if (typeof timeInput.value.showPicker === 'function') {
    try {
      timeInput.value.showPicker()
      return
    } catch {
      // Focus the input when the browser does not allow opening its picker.
    }
  }
  timeInput.value.focus()
}

function saveTime() {
  if (!timeDraft.value) return
  deadlineTime.value = timeDraft.value
  showTimePicker.value = false
}

function saveDeadline() {
  if (!deadlineDate.value || !deadlineTime.value || (props.showTitle && !taskTitle.value.trim())) return
  emit('save', {
    title: taskTitle.value.trim(),
    date: deadlineDate.value,
    time: deadlineTime.value,
  })
}
</script>

<template>
  <Transition name="deadline-modal">
    <div
      v-if="open"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 p-3 backdrop-blur-sm sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-labelledby="deadline-title"
      @click.self="emit('close')"
    >
      <form
        class="w-full max-w-[800px] rounded-2xl bg-white shadow-2xl"
        @submit.prevent="saveDeadline"
      >
        <header
          class="relative flex min-h-20 items-center justify-center rounded-t-2xl bg-[linear-gradient(105deg,#2864E8_0%,#173C87_100%)] px-14 py-5 text-center text-white sm:min-h-[104px] sm:px-20"
        >
          <h2 id="deadline-title" class="text-xl font-bold sm:text-2xl">
            {{ showTitle ? 'Atur Judul & Tenggat Tugas' : 'Tentukan Tenggat Waktu' }}
          </h2>
          <button
            type="button"
            class="absolute right-4 top-1/2 flex size-10 -translate-y-1/2 items-center justify-center text-white transition hover:scale-110 sm:right-8 sm:size-12"
            aria-label="Tutup pengaturan tenggat waktu"
            @click="emit('close')"
          >
            <svg class="size-8 sm:size-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.75"
                d="M6 6l12 12M18 6L6 18"
              />
            </svg>
          </button>
        </header>

        <div class="space-y-5 rounded-b-2xl px-5 py-7 sm:px-10 sm:py-9">
          <label v-if="showTitle" class="block">
            <span class="mb-2 block text-base font-medium text-[#888888] sm:text-2xl">Judul Tugas</span>
            <input
              v-model="taskTitle"
              type="text"
              maxlength="120"
              placeholder="Masukkan judul tugas"
              required
              class="h-[68px] w-full rounded-2xl border border-[#888888] bg-white px-4 text-lg font-medium text-black outline-none transition placeholder:text-[#999999] focus:border-[#2864E8] focus:ring-2 focus:ring-[#2864E8]/20 sm:h-[78px] sm:px-5 sm:text-2xl"
            />
          </label>

          <label class="block">
            <span class="mb-2 block text-base font-medium text-[#888888] sm:text-2xl">Tanggal</span>
            <span class="relative block">
              <button
                type="button"
                class="flex h-[68px] w-full items-center justify-between rounded-2xl border border-[#888888] bg-white px-4 text-left text-lg font-medium text-black outline-none transition hover:border-[#2864E8] focus-visible:border-[#2864E8] focus-visible:ring-2 focus-visible:ring-[#2864E8]/20 sm:h-[78px] sm:px-5 sm:text-2xl"
                aria-label="Pilih tanggal"
                :aria-expanded="showDatePicker"
                aria-haspopup="dialog"
                @click="toggleDatePicker"
              >
                <span>{{ selectedDateLabel }}</span>
                <img :src="calendarIcon" alt="" class="size-7 shrink-0 sm:size-10" />
              </button>
              <div
                v-if="showDatePicker"
                class="absolute left-0 top-[calc(100%+8px)] z-20 w-full max-w-[360px] rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_16px_40px_rgba(15,23,42,0.2)] sm:p-5"
                role="dialog"
                aria-label="Pilih tanggal tenggat"
              >
                <div class="mb-4 flex items-center justify-between">
                  <button
                    type="button"
                    class="flex size-9 items-center justify-center rounded-full text-slate-600 transition hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-[#2864E8]"
                    aria-label="Bulan sebelumnya"
                    @click="changeMonth(-1)"
                  >
                    <span aria-hidden="true">‹</span>
                  </button>
                  <p class="text-base font-semibold capitalize text-slate-800">
                    {{ visibleMonthLabel }}
                  </p>
                  <button
                    type="button"
                    class="flex size-9 items-center justify-center rounded-full text-slate-600 transition hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-[#2864E8]"
                    aria-label="Bulan berikutnya"
                    @click="changeMonth(1)"
                  >
                    <span aria-hidden="true">›</span>
                  </button>
                </div>
                <div class="grid grid-cols-7 gap-y-1 text-center">
                  <span
                    v-for="(weekday, index) in ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']"
                    :key="index"
                    class="pb-2 text-xs font-semibold text-slate-500"
                  >
                    {{ weekday }}
                  </span>
                  <button
                    v-for="day in calendarDays"
                    :key="day.value"
                    type="button"
                    :disabled="day.value < minDate"
                    :aria-label="new Intl.DateTimeFormat('id-ID', { dateStyle: 'full' }).format(day.date)"
                    :aria-pressed="day.value === deadlineDate"
                    class="mx-auto flex size-9 items-center justify-center rounded-full text-sm transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#2864E8] disabled:cursor-not-allowed disabled:text-slate-300"
                    :class="[
                      day.inMonth ? 'text-slate-700' : 'text-slate-300',
                      day.value === deadlineDate
                        ? 'bg-[#2864E8] font-semibold text-white hover:bg-[#1f52c4]'
                        : 'hover:bg-blue-50',
                    ]"
                    @click="selectDate(day)"
                  >
                    {{ day.day }}
                  </button>
                </div>
              </div>
            </span>
          </label>

          <label class="block">
            <span class="mb-2 block text-base font-medium text-[#888888] sm:text-2xl">Waktu</span>
            <span class="relative block">
              <button
                type="button"
                class="flex h-[68px] w-full items-center justify-between rounded-2xl border border-[#888888] bg-white px-4 text-left text-lg font-medium text-black outline-none transition hover:border-[#2864E8] focus-visible:border-[#2864E8] focus-visible:ring-2 focus-visible:ring-[#2864E8]/20 sm:h-[78px] sm:px-5 sm:text-2xl"
                aria-label="Pilih waktu"
                :aria-expanded="showTimePicker"
                aria-haspopup="dialog"
                @click="toggleTimePicker"
              >
                <span>{{ deadlineTime }} <span class="text-sm font-medium text-[#888888] sm:text-lg">WIB</span></span>
                <img :src="clockIcon" alt="" class="size-7 shrink-0 sm:size-10" />
              </button>
              <div
                v-if="showTimePicker"
                class="absolute left-0 top-[calc(100%+8px)] z-20 w-full max-w-[360px] rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_16px_40px_rgba(15,23,42,0.2)] sm:p-5"
                role="dialog"
                aria-label="Pilih waktu WIB"
              >
                <div class="flex items-end gap-3">
                  <label class="min-w-0 flex-1">
                    <span class="mb-2 block text-sm font-medium text-slate-600">Waktu (WIB)</span>
                    <input
                      ref="timeInput"
                      v-model="timeDraft"
                      type="time"
                      required
                      class="h-12 w-full rounded-xl border border-slate-300 bg-white px-3 text-lg font-medium text-slate-900 outline-none focus:border-[#2864E8] focus:ring-2 focus:ring-[#2864E8]/20"
                    />
                  </label>
                  <button
                    type="button"
                    class="h-12 rounded-xl bg-[#2864E8] px-5 text-sm font-semibold text-white transition hover:bg-[#1f52c4]"
                    @click="saveTime"
                  >
                    Pilih
                  </button>
                </div>
              </div>
            </span>
          </label>

          <div class="flex justify-end pt-1 sm:pt-2">
            <button
              type="submit"
              class="min-h-14 w-full rounded-2xl bg-[#2864E8] px-10 text-lg font-semibold text-white transition hover:bg-[#1f50be] active:scale-[0.98] sm:min-h-[60px] sm:w-auto sm:min-w-[180px] sm:text-xl"
            >
              Selesai
            </button>
          </div>
        </div>
      </form>
    </div>
  </Transition>
</template>

<style scoped>
.deadline-modal-enter-active,
.deadline-modal-leave-active {
  transition: opacity 0.2s ease;
}

.deadline-modal-enter-from,
.deadline-modal-leave-to {
  opacity: 0;
}

input[type='time']::-webkit-calendar-picker-indicator {
  cursor: pointer;
}
</style>
