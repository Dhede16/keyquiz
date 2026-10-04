<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import TextField from '@/components/ui/TextField.vue'
import SelectField from '@/components/ui/SelectField.vue'

const email = ref('')
const fullName = ref('')
const password = ref('')
const confirmPassword = ref('')
const role = ref('')
const errorMsg = ref('')
const loading = ref(false)

const router = useRouter()
const { register } = useAuth()

const roles = [
  { value: 'teacher', label: 'Dosen' },
  { value: 'student', label: 'Mahasiswa' },
]

const mismatch = computed(
  () => confirmPassword.value !== '' && password.value !== confirmPassword.value,
)

async function onSubmit() {
  if (mismatch.value || !role.value) return
  if (!email.value || !password.value || !fullName.value) {
    errorMsg.value = 'Semua field wajib diisi.'
    return
  }
  if (password.value.length < 6) {
    errorMsg.value = 'Kata sandi minimal 6 karakter.'
    return
  }

  errorMsg.value = ''
  loading.value = true

  try {
    await register({
      email: email.value,
      password: password.value,
      name: fullName.value,
      role: role.value,
    })
    router.push({
      path: '/login',
      query: {
        registered: 'true',
        email: email.value.trim(),
        role: role.value,
      },
    })
  } catch (err) {
    errorMsg.value = err.message || 'Gagal mendaftar. Silakan coba lagi.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div
    class="w-full rounded-[2rem] border border-[#222222] bg-white p-6 sm:rounded-[2.75rem] sm:p-10"
  >
    <h2 class="text-xl font-semibold text-[#111111] sm:text-3xl">Daftar ke KeyQuiz</h2>

    <div
      v-if="errorMsg"
      class="mt-4 rounded-xl border border-red-200 bg-red-50 p-3.5 text-sm font-medium text-red-700"
      role="alert"
    >
      {{ errorMsg }}
    </div>

    <form class="mt-6 space-y-4 sm:mt-8 sm:space-y-5" @submit.prevent="onSubmit">
      <TextField id="email" v-model="email" label="Email" type="email" autocomplete="email" required />
      <TextField id="fullName" v-model="fullName" label="Nama Lengkap" autocomplete="name" required />

      <!-- kata sandi & konfirmasi berdampingan -->
      <div class="grid grid-cols-1 gap-4 min-[480px]:grid-cols-2 sm:gap-3">
        <TextField
          id="password"
          v-model="password"
          label="Kata Sandi"
          type="password"
          autocomplete="new-password"
          required
        />
        <TextField
          id="confirmPassword"
          v-model="confirmPassword"
          label="Konfirmasi Kata Sandi"
          type="password"
          autocomplete="new-password"
          required
        />
      </div>
      <p v-if="mismatch" class="-mt-2 text-sm text-red-600" role="alert">
        Kata sandi dan konfirmasi belum sama.
      </p>

      <SelectField
        id="role"
        v-model="role"
        label="Pilih Peran"
        placeholder="Pilih Peran"
        :options="roles"
        required
      />

      <button
        type="submit"
        :disabled="loading || mismatch || !role"
        class="motion-control mt-2 h-12 w-full cursor-pointer rounded-lg border border-[#1f52c4] bg-[#2864E8] text-base font-semibold text-white transition hover:bg-[#1f52c4] disabled:opacity-60 disabled:cursor-not-allowed sm:h-14 sm:text-lg flex items-center justify-center gap-2"
      >
        <span v-if="loading" class="inline-block h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
        <span>{{ loading ? 'Mendaftarkan...' : 'Daftar' }}</span>
      </button>

      <p class="text-center text-sm text-[#777777]">
        Sudah punya akun?
        <RouterLink to="/login" class="font-semibold text-[#2864E8] hover:underline"
          >Masuk</RouterLink
        >
      </p>
    </form>
  </div>
</template>
