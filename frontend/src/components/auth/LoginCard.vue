<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import TextField from '@/components/ui/TextField.vue'
import SelectField from '@/components/ui/SelectField.vue'

const email = ref('')
const password = ref('')
const role = ref('teacher')
const errorMsg = ref('')
const loading = ref(false)

const roles = [
  { value: 'teacher', label: 'Dosen' },
  { value: 'student', label: 'Mahasiswa' },
]

const router = useRouter()
const { login } = useAuth()

async function onSubmit() {
  if (!email.value || !password.value) {
    errorMsg.value = 'Email dan kata sandi wajib diisi.'
    return
  }

  errorMsg.value = ''
  loading.value = true

  try {
    await login({ email: email.value, password: password.value, role: role.value })
    router.push('/beranda')
  } catch (err) {
    errorMsg.value = err.message || 'Gagal masuk. Periksa email dan kata sandi Anda.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div
    class="w-full rounded-[2rem] border border-[#222222] bg-white p-6 sm:rounded-[2.75rem] sm:p-10"
  >
    <h2 class="text-xl font-semibold text-[#111111] sm:text-3xl">Masuk ke KeyQuiz</h2>

    <div
      v-if="errorMsg"
      class="mt-4 rounded-xl border border-red-200 bg-red-50 p-3.5 text-sm font-medium text-red-700"
      role="alert"
    >
      {{ errorMsg }}
    </div>

    <form class="mt-6 space-y-4 sm:mt-8 sm:space-y-5" @submit.prevent="onSubmit">
      <TextField id="email" v-model="email" label="Email" type="email" autocomplete="email" required />
      <TextField
        id="password"
        v-model="password"
        label="Kata Sandi"
        type="password"
        autocomplete="current-password"
        required
      />
      <SelectField id="login-role" v-model="role" label="Masuk sebagai" :options="roles" />

      <div class="text-right">
        <a href="#" class="text-sm font-semibold text-[#2864E8] hover:underline sm:text-base"
          >Lupa kata sandi</a
        >
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="motion-control h-12 w-full cursor-pointer rounded-lg border border-[#1f52c4] bg-[#2864E8] text-base font-semibold text-white transition hover:bg-[#1f52c4] disabled:opacity-60 disabled:cursor-not-allowed sm:h-14 sm:text-lg flex items-center justify-center gap-2"
      >
        <span v-if="loading" class="inline-block h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
        <span>{{ loading ? 'Memproses...' : 'Masuk' }}</span>
      </button>

      <p class="text-center text-sm text-[#777777]">
        Belum punya akun?
        <RouterLink to="/daftar" class="font-semibold text-[#2864E8] hover:underline"
          >Daftar</RouterLink
        >
      </p>
    </form>
  </div>
</template>
