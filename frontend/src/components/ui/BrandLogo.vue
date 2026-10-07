<script setup>
import logo from '@/assets/logo-dashboard.svg'

defineProps({
  landing: Boolean,
})
</script>

<template>
  <RouterLink
    to="/"
    aria-label="KeyQuiz"
    class="relative -left-6 inline-block"
    :class="landing ? 'sm:-left-6' : 'sm:-left-2.5'"
  >
    <img
      :src="logo"
      alt="KeyQuiz"
      class="relative top-3 -my-8 w-44 sm:top-2.5 sm:my-0"
      :class="landing ? 'sm:w-[220px]' : 'sm:w-40'"
    />
  </RouterLink>
</template>
