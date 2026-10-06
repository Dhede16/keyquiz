<script setup>
import { ref } from 'vue'

defineProps({
  id: { type: String, required: true },
  label: { type: String, required: true },
  type: { type: String, default: 'text' },
  autocomplete: { type: String, default: undefined },
  revealPassword: { type: Boolean, default: false },
})
const model = defineModel({ type: String, default: '' })
const passwordVisible = ref(false)
</script>

<template>
  <div>
    <label :for="id" class="mb-1.5 block text-xs font-medium text-[#777777] sm:text-sm">{{ label }}</label>
    <div class="relative">
      <input
        :id="id"
        v-model="model"
        :type="revealPassword && passwordVisible ? 'text' : type"
        :autocomplete="autocomplete"
        required
        class="h-12 w-full rounded-lg border border-[#8a8a8a] bg-white px-4 text-sm text-[#222222] outline-none transition focus:border-[#2864E8] focus:ring-2 focus:ring-[#2864E8]/25 sm:h-14 sm:text-base"
        :class="{ 'pr-12': revealPassword }"
      />
      <button
        v-if="revealPassword"
        type="button"
        class="absolute inset-y-0 right-0 flex w-12 items-center justify-center rounded-r-lg text-[#555555] hover:text-[#2864E8] focus-visible:outline-2 focus-visible:outline-offset-[-3px] focus-visible:outline-[#2864E8]"
        :aria-label="passwordVisible ? 'Sembunyikan kata sandi' : 'Lihat kata sandi'"
        :aria-pressed="passwordVisible"
        @click="passwordVisible = !passwordVisible"
      >
        <svg
          v-if="passwordVisible"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <path d="M3 3l18 18M10.6 10.7a2 2 0 002.7 2.7M9.9 5.2A10.8 10.8 0 0112 5c5.5 0 9 7 9 7a14.8 14.8 0 01-3.2 3.8M6.2 6.2C3.9 7.8 3 12 3 12s3.5 7 9 7a9.8 9.8 0 004.1-.9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <svg
          v-else
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <path d="M3 12s3.5-7 9-7 9 7 9 7-3.5 7-9 7-9-7-9-7z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
          <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.8" />
        </svg>
      </button>
    </div>
  </div>
</template>
