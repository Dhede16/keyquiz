import { computed, ref } from 'vue'
import { supabase } from '@/services/supabase.js'
import { registerAdminAPI } from '@/services/api.js'

const STORAGE_KEY = 'keyquiz:user'

function loadLocalUser() {
  let storedUser
  try {
    storedUser = JSON.parse(localStorage.getItem(STORAGE_KEY)) || null
  } catch {
    return null
  }

  if (storedUser && typeof storedUser === 'object' && 'password' in storedUser) {
    delete storedUser.password
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(storedUser))
    } catch {
      /* storage tidak tersedia */
    }
  }
  return storedUser
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

async function loadUserData(authUser) {
  const [{ data: profile, error: profileError }, { data: privateProfile, error: privateError }] =
    await Promise.all([
      supabase
        .from('profiles')
        .select('name, role, avatar_url')
        .eq('id', authUser.id)
        .maybeSingle(),
      supabase
        .from('profile_private')
        .select('birth_date, phone, gender')
        .eq('user_id', authUser.id)
        .maybeSingle(),
    ])

  if (profileError) throw profileError
  if (privateError) throw privateError

  return {
    id: authUser.id,
    email: authUser.email,
    name: profile?.name || authUser.user_metadata?.name || nameFromEmail(authUser.email || ''),
    role: profile?.role || 'student',
    avatarUrl: profile?.avatar_url || '',
    birthDate: privateProfile?.birth_date || '',
    phone: privateProfile?.phone || '',
    gender: privateProfile?.gender || '',
  }
}

// Inisialisasi session dari Supabase Auth saat aplikasi dimulai
async function initAuthSession() {
  try {
    const { data: { session } } = await supabase.auth.getSession()
    if (session?.user) {
      saveLocalUser(await loadUserData(session.user))
    }
  } catch (err) {
    console.warn('[Supabase Auth] Sesi lokal tetap digunakan:', err.message)
  }
}

// Pantau perubahan status autentikasi di Supabase
supabase.auth.onAuthStateChange(async (event, session) => {
  if (event === 'SIGNED_IN' && session?.user) {
    try {
      saveLocalUser(await loadUserData(session.user))
    } catch (err) {
      console.warn('[Supabase Auth] Gagal memuat profil:', err.message)
    }
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
  async function login({ email, password }) {
    authLoading.value = true
    try {
      if (!email?.trim() || !password) {
        throw new Error('Email dan kata sandi wajib diisi.')
      }

      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      })

      if (error) {
        if (error.message.includes('Invalid login credentials')) {
          throw new Error('Email atau kata sandi salah. Silakan periksa kembali atau daftar akun baru.')
        }
        throw error
      }

      if (data?.user) {
        const userData = await loadUserData(data.user)
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
      await registerAdminAPI({
        email: trimmedEmail,
        password,
        name: displayName,
        role,
      })

      await supabase.auth.signOut().catch(() => {})
      saveLocalUser(null)
      return { success: true, email: trimmedEmail }
    } finally {
      authLoading.value = false
    }
  }

  async function updateProfile({ name, birthDate, phone, gender, avatarFile }) {
    if (!user.value?.id) {
      throw new Error('Sesi pengguna tidak ditemukan. Silakan masuk kembali.')
    }

    const {
      data: { user: authUser },
      error: authError,
    } = await supabase.auth.getUser()
    if (authError) throw authError
    if (!authUser) {
      throw new Error('Sesi pengguna tidak ditemukan. Silakan masuk kembali.')
    }
    if (user.value.id !== authUser.id) {
      throw new Error('Akun sesi berubah. Muat ulang halaman sebelum menyimpan profil.')
    }

    let avatarUrl = user.value.avatarUrl || ''
    if (avatarFile) {
      const avatarPath = `${authUser.id}/avatar.jpg`
      const { error: uploadError } = await supabase.storage
        .from('profile')
        .upload(avatarPath, avatarFile, {
          cacheControl: '0',
          contentType: 'image/jpeg',
          upsert: true,
        })
      if (uploadError) throw uploadError

      const { data: publicUrlData } = supabase.storage.from('profile').getPublicUrl(avatarPath)
      avatarUrl = publicUrlData.publicUrl
    }

    const profileData = {
      profile_name: name.trim(),
      profile_avatar_url: avatarUrl || null,
      private_birth_date: birthDate || null,
      private_phone: phone.trim() || null,
      private_gender: gender || null,
    }
    const { error: updateError } = await supabase.rpc('update_own_profile', profileData)
    if (updateError) throw updateError

    const userData = {
      ...user.value,
      name: profileData.profile_name,
      avatarUrl: profileData.profile_avatar_url || '',
      birthDate: profileData.private_birth_date || '',
      phone: profileData.private_phone || '',
      gender: profileData.private_gender || '',
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
