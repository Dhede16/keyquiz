import { computed, ref } from 'vue'
import { supabase } from '@/services/supabase.js'
import { registerAdminAPI } from '@/services/api.js'

const STORAGE_KEY = 'keyquiz:user'

function loadLocalUser() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || null
  } catch {
    return null
  }
}

const user = ref(loadLocalUser())
const authLoading = ref(false)

function saveLocalUser(userData) {
  user.value = userData
  try {
    if (userData) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(userData))
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  } catch {
    /* storage tidak tersedia */
  }
}

function nameFromEmail(email) {
  const base = email
    .split('@')[0]
    .replace(/[._-]+/g, ' ')
    .trim()
  return base ? base.replace(/\b\w/g, (c) => c.toUpperCase()) : 'Pengguna'
}

// Inisialisasi session dari Supabase Auth saat aplikasi dimulai
async function initAuthSession() {
  try {
    const { data: { session } } = await supabase.auth.getSession()
    if (session?.user) {
      // Ambil detail profile dari tabel profiles
      const { data: profile } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', session.user.id)
        .single()

      const userData = {
        id: session.user.id,
        email: session.user.email,
        name: profile?.name || session.user.user_metadata?.name || nameFromEmail(session.user.email),
        role: profile?.role || session.user.user_metadata?.role || 'student',
        password: profile?.password || session.user.user_metadata?.password || '',
        birthDate: profile?.birth_date || '',
        phone: profile?.phone || '',
        gender: profile?.gender || '',
      }
      saveLocalUser(userData)
    }
  } catch (err) {
    console.warn('[Supabase Auth] Sesi lokal tetap digunakan:', err.message)
  }
}

// Pantau perubahan status autentikasi di Supabase
supabase.auth.onAuthStateChange(async (event, session) => {
  if (event === 'SIGNED_IN' && session?.user) {
    const { data: profile } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', session.user.id)
      .single()

    const userData = {
      id: session.user.id,
      email: session.user.email,
      name: profile?.name || session.user.user_metadata?.name || nameFromEmail(session.user.email),
      role: profile?.role || session.user.user_metadata?.role || 'student',
      password: profile?.password || session.user.user_metadata?.password || '',
      birthDate: profile?.birth_date || '',
      phone: profile?.phone || '',
      gender: profile?.gender || '',
    }
    saveLocalUser(userData)
  } else if (event === 'SIGNED_OUT') {
    saveLocalUser(null)
  }
})

// Jalankan inisialisasi sesi di background
initAuthSession()

export function useAuth() {
  const isLoggedIn = computed(() => !!user.value)

  /**
   * Login pengguna via Supabase Auth.
   */
  async function login({ email, password, role }) {
    authLoading.value = true
    try {
      if (password) {
        const { data, error } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        })

        if (error) {
          // Jika user belum ada di Supabase auth (misal demo user), kita coba daftarkan otomatis atau login demo
          if (error.message.includes('Invalid login credentials')) {
            throw new Error('Email atau kata sandi salah. Silakan periksa kembali atau daftar akun baru.')
          }
          throw error
        }

        if (data?.user) {
          const { data: profile } = await supabase
            .from('profiles')
            .select('*')
            .eq('id', data.user.id)
            .single()

          const userData = {
            id: data.user.id,
            email: data.user.email,
            name: profile?.name || data.user.user_metadata?.name || nameFromEmail(email),
            role: profile?.role || role || data.user.user_metadata?.role || 'teacher',
            password: profile?.password || password || '',
            birthDate: profile?.birth_date || '',
            phone: profile?.phone || '',
            gender: profile?.gender || '',
          }
          saveLocalUser(userData)
          return userData
        }
      } else {
        // Fallback untuk mode tanpa password jika diperlukan
        const userData = {
          id: user.value?.id || `usr-${Date.now()}`,
          email: email.trim(),
          name: nameFromEmail(email),
          role: role || user.value?.role || 'teacher',
        }
        saveLocalUser(userData)
        return userData
      }
    } finally {
      authLoading.value = false
    }
  }

  /**
   * Registrasi akun baru di Supabase Auth & tabel profiles.
   */
  async function register({ email, password, name, role = 'student' }) {
    authLoading.value = true
    try {
      const trimmedEmail = email.trim()
      const displayName = name?.trim() || nameFromEmail(trimmedEmail)

      let authUser = null

      try {
        const { data, error } = await supabase.auth.signUp({
          email: trimmedEmail,
          password,
          options: {
            data: {
              name: displayName,
              role,
              password,
            },
          },
        })

        if (error) throw error
        authUser = data?.user
      } catch (signUpErr) {
        const msg = (signUpErr.message || '').toLowerCase()
        // Jika terkena email rate limit / pembatasan email Supabase, fallback langsung ke backend admin register
        if (
          msg.includes('rate limit') ||
          msg.includes('over_email_send_rate_limit') ||
          msg.includes('exceeded') ||
          msg.includes('email')
        ) {
          console.warn('[useAuth] Email rate limit terdeteksi, beralih ke Backend Admin registration...')
          await registerAdminAPI({
            email: trimmedEmail,
            password,
            name: displayName,
            role,
          })

          // Otomatis login dengan kredensial yang baru dibuat
          return await login({ email: trimmedEmail, password, role })
        }
        throw signUpErr
      }

      if (authUser) {
        // Pastikan record profil terisi (trigger akan handle, tapi upsert memastikan keamanan)
        await supabase.from('profiles').upsert({
          id: authUser.id,
          email: trimmedEmail,
          name: displayName,
          role,
          password,
        })

        const userData = {
          id: authUser.id,
          email: trimmedEmail,
          name: displayName,
          role,
          password,
          birthDate: '',
          phone: '',
          gender: '',
        }
        saveLocalUser(userData)
        return userData
      }
    } finally {
      authLoading.value = false
    }
  }

  async function updateProfile({ name, birthDate, phone, gender }) {
    if (!user.value?.id) {
      throw new Error('Sesi pengguna tidak ditemukan. Silakan masuk kembali.')
    }

    const { data, error } = await supabase
      .from('profiles')
      .update({
        name: name.trim(),
        birth_date: birthDate || null,
        phone: phone.trim() || null,
        gender: gender || null,
      })
      .eq('id', user.value.id)
      .select('name, birth_date, phone, gender')
      .single()

    if (error) throw error

    const userData = {
      ...user.value,
      name: data.name,
      birthDate: data.birth_date || '',
      phone: data.phone || '',
      gender: data.gender || '',
    }
    saveLocalUser(userData)
    return userData
  }

  /**
   * Keluar dari sesi aplikasi & Supabase Auth.
   */
  async function logout() {
    authLoading.value = true
    try {
      await supabase.auth.signOut()
    } catch (err) {
      console.warn('[Supabase Auth] SignOut error:', err.message)
    } finally {
      saveLocalUser(null)
      authLoading.value = false
    }
  }

  return {
    user,
    isLoggedIn,
    authLoading,
    login,
    register,
    updateProfile,
    logout,
  }
}
