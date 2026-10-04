import { ref } from 'vue'
import { classes as initialClasses } from '@/data/classes.js'
import { supabase } from '@/services/supabase.js'
import { saveEssayKey } from '@/services/api.js'

const CLASSES_STORAGE_KEY = 'keyquiz:classes'
const classes = ref(loadInitialClasses())
const isSyncing = ref(false)

function loadInitialClasses() {
  try {
    const stored = JSON.parse(localStorage.getItem(CLASSES_STORAGE_KEY))
    return Array.isArray(stored) && stored.length > 0 ? stored : [...initialClasses]
  } catch {
    return [...initialClasses]
  }
}

function saveLocal() {
  try {
    localStorage.setItem(CLASSES_STORAGE_KEY, JSON.stringify(classes.value))
  } catch {
    // Local storage fallback
  }
}

function membershipStorageKey(email) {
  return `keyquiz:joined-classes:${encodeURIComponent(email ? email.trim().toLowerCase() : 'anonymous')}`
}

function getMemberships(email) {
  if (!email) return []
  try {
    const memberships = JSON.parse(localStorage.getItem(membershipStorageKey(email)))
    return Array.isArray(memberships) ? memberships : []
  } catch {
    return []
  }
}

function getClassesForStudent(email, studentId = null) {
  if (!email && !studentId) return []
  const memberships = new Set(getMemberships(email).map(String))
  const cleanEmail = email ? email.trim().toLowerCase() : ''

  return classes.value.filter((classItem) => {
    if (memberships.has(String(classItem.id))) return true
    if (classItem.code && memberships.has(String(classItem.code).toUpperCase())) return true
    if (Array.isArray(classItem.members)) {
      if (studentId && classItem.members.some((m) => m.studentId === studentId || m.id === studentId)) {
        return true
      }
      if (cleanEmail && classItem.members.some((m) => m.email?.trim().toLowerCase() === cleanEmail)) {
        return true
      }
    }
    return false
  })
}

function getClassesForTeacher(email, teacherId = null, teacherName = null) {
  const cleanEmail = email ? email.trim().toLowerCase() : ''
  const cleanName = teacherName ? teacherName.trim().toLowerCase() : ''

  return classes.value.filter((classItem) => {
    if (teacherId && (classItem.teacherId === teacherId || classItem.teacher_id === teacherId)) {
      return true
    }
    if (cleanEmail && ((classItem.teacherEmail && classItem.teacherEmail.toLowerCase() === cleanEmail) || (classItem.email && classItem.email.toLowerCase() === cleanEmail))) {
      return true
    }
    if (cleanName && classItem.lecturer && classItem.lecturer.toLowerCase().includes(cleanName)) {
      return true
    }
    return false
  })
}

/**
 * Sinkronisasi data kelas & tugas dari Supabase ke state aplikasi.
 */
async function syncClassesFromSupabase(userEmail = null) {
  if (isSyncing.value) return
  isSyncing.value = true

  try {
    const { data: { user } } = await supabase.auth.getUser()

    // 1. Ambil data kelas beserta anggota_kelas, tugas, soal, opsi, kunci, jawaban_mahasiswa, dan detail_jawaban
    const { data: dbClasses, error: classErr } = await supabase
      .from('kelas')
      .select(`
        id,
        teacher_id,
        title,
        major,
        description,
        code,
        created_at,
        profiles:teacher_id (
          id,
          email,
          name
        ),
        anggota_kelas (
          id,
          student_id,
          joined_at,
          profiles (
            id,
            email,
            name
          )
        ),
        tugas (
          id,
          title,
          description,
          deadline,
          status,
          show_score,
          show_correct_answers,
          created_at,
          soal (
            id,
            type,
            question_text,
            points,
            order_index,
            opsi_jawaban (
              id,
              option_letter,
              option_text,
              is_correct,
              order_index
            ),
            kunci_jawaban_essay (
              id,
              answer_key,
              rubric
            )
          ),
          jawaban_mahasiswa (
            id,
            student_id,
            status,
            total_score,
            is_scanned,
            submitted_at,
            graded_at,
            profiles (
              id,
              email,
              name
            ),
            detail_jawaban (
              id,
              soal_id,
              opsi_jawaban_id,
              jawaban_teks,
              similarity_score,
              rubric_evaluation,
              nilai_ai,
              nilai_final,
              teacher_feedback
            )
          )
        )
      `)
      .order('created_at', { ascending: false })

    if (classErr) throw classErr

    if (dbClasses && dbClasses.length > 0) {
      const emailToCheck = userEmail || user?.email

      // Jika user terautentikasi sebagai siswa, sinkronkan keanggotaan kelas dari tabel anggota_kelas
      if (emailToCheck && user) {
        const studentJoinedClassIds = dbClasses
          .filter((c) => (c.anggota_kelas || []).some((ak) => ak.student_id === user.id || ak.profiles?.email?.toLowerCase() === emailToCheck.toLowerCase()))
          .map((c) => String(c.id))

        if (studentJoinedClassIds.length > 0) {
          const currentLocal = getMemberships(emailToCheck)
          const merged = Array.from(new Set([...currentLocal.map(String), ...studentJoinedClassIds]))
          localStorage.setItem(membershipStorageKey(emailToCheck), JSON.stringify(merged))
        }
      }

      const formattedClasses = dbClasses.map((c) => {
        const formattedMembers = (c.anggota_kelas || []).map((ak) => ({
          id: ak.id,
          studentId: ak.student_id,
          joinedAt: ak.joined_at,
          email: ak.profiles?.email || '',
          name: ak.profiles?.name || 'Mahasiswa',
        }))

        const formattedTasks = (c.tugas || []).map((t) => {
          const deadlineObj = t.deadline ? new Date(t.deadline) : null
          const formattedQuestions = (t.soal || [])
            .sort((a, b) => (a.order_index || 0) - (b.order_index || 0))
            .map((s) => {
              const options = (s.opsi_jawaban || [])
                .sort((a, b) => (a.order_index || 0) - (b.order_index || 0))
                .map((o) => o.option_text)

              const correctOpt = (s.opsi_jawaban || []).find((o) => o.is_correct)
              const essayKey = s.kunci_jawaban_essay?.[0] || s.kunci_jawaban_essay

              return {
                id: s.id,
                title: s.question_text,
                type: s.type,
                points: Number(s.points) || 10,
                options,
                answerKey: correctOpt ? correctOpt.option_text : essayKey?.answer_key || '',
                rubric: essayKey?.rubric || [],
              }
            })

          const formattedSubmissions = (t.jawaban_mahasiswa || []).map((jm) => ({
            id: jm.id,
            studentId: jm.student_id,
            email: jm.profiles?.email || '',
            name: jm.profiles?.name || 'Mahasiswa',
            score: jm.total_score,
            graded: jm.status === 'graded',
            submittedAt: jm.submitted_at,
            answers: (jm.detail_jawaban || []).map((dj) => ({
              id: dj.id,
              questionId: dj.soal_id,
              value: dj.jawaban_teks,
              score: dj.nilai_final ?? dj.nilai_ai,
              feedback: dj.teacher_feedback,
              rubricEvaluation: dj.rubric_evaluation,
            })),
          }))

          return {
            id: t.id,
            title: t.title,
            description: t.description || '',
            status: t.status,
            showScore: t.show_score,
            showCorrectAnswers: t.show_correct_answers,
            date: deadlineObj
              ? deadlineObj.toLocaleDateString('id-ID', {
                  weekday: 'long',
                  day: 'numeric',
                  month: 'long',
                  year: 'numeric',
                })
              : 'Tidak ada batas',
            dueAt: t.deadline,
            questions: formattedQuestions,
            submissions: formattedSubmissions,
          }
        })

        return {
          id: c.id,
          teacherId: c.teacher_id,
          teacherEmail: c.profiles?.email || '',
          lecturer: c.profiles?.name || 'Dosen',
          title: c.title,
          major: c.major || '',
          description: c.description || '',
          code: c.code,
          members: formattedMembers,
          tasks: formattedTasks,
        }
      })

      classes.value = formattedClasses
      saveLocal()
    }
  } catch (err) {
    console.warn('[Supabase DB Sync] Mempertahankan state lokal:', err.message)
  } finally {
    isSyncing.value = false
  }
}

/**
 * Tambah kelas baru & simpan ke Supabase `kelas`.
 */
async function addClass(classItem) {
  let code = classItem.code
  while (!code || classes.value.some((existingClass) => existingClass.code === code)) {
    code = `KQ-${Math.random().toString(36).slice(2, 8).toUpperCase()}`
  }

  let teacherId = classItem.teacherId || null
  let teacherEmail = classItem.teacherEmail || null
  let lecturerName = classItem.lecturer || 'Dosen'

  try {
    const { data: { user } } = await supabase.auth.getUser()
    if (user) {
      teacherId = user.id
      teacherEmail = user.email
      lecturerName = user.user_metadata?.name || lecturerName
    }
  } catch {}

  const newClass = {
    ...classItem,
    id: classItem.id || crypto.randomUUID(),
    code,
    teacherId,
    teacherEmail,
    lecturer: lecturerName,
    members: classItem.members || [],
    tasks: classItem.tasks || [],
  }

  classes.value.unshift(newClass)
  saveLocal()

  // Kirim ke Supabase jika terautentikasi
  if (teacherId) {
    try {
      await supabase.from('kelas').insert({
        id: newClass.id,
        teacher_id: teacherId,
        title: newClass.title,
        major: newClass.major || null,
        description: newClass.description || null,
        code: newClass.code,
      })
    } catch (err) {
      console.warn('[Supabase DB] Simpan kelas gagal:', err.message)
    }
  }

  return newClass
}

/**
 * Tambah tugas dan butir soal ke kelas & simpan ke Supabase (`tugas`, `soal`, `opsi_jawaban`, `kunci_jawaban_essay`).
 */
async function addTaskToClass(classId, task) {
  const classItem = classes.value.find((item) => String(item.id) === String(classId))
  if (!classItem) return null

  const taskId = task.id || crypto.randomUUID()
  const newTask = {
    showScore: true,
    showCorrectAnswers: false,
    submissions: [],
    ...task,
    id: taskId,
  }

  classItem.tasks ||= []
  classItem.tasks.push(newTask)
  saveLocal()

  // Simpan ke Supabase di background
  ;(async () => {
    try {
      // 1. Insert ke tabel `tugas`
      const { data: createdTask, error: taskErr } = await supabase
        .from('tugas')
        .insert({
          id: newTask.id,
          kelas_id: classItem.id,
          title: newTask.title,
          description: newTask.description || null,
          deadline: newTask.dueAt || null,
          status: newTask.status || 'published',
          show_score: newTask.showScore ?? true,
          show_correct_answers: newTask.showCorrectAnswers ?? false,
        })
        .select()
        .single()

      if (taskErr) {
        console.warn('[Supabase DB] Error insert tugas:', taskErr.message)
        return
      }

      // 2. Insert tiap butir soal ke tabel `soal` & opsi/kunci
      for (let i = 0; i < (newTask.questions || []).length; i++) {
        const q = newTask.questions[i]
        // Selalu generate UUID baru untuk soal — ID lokal (Date.now) bukan valid UUID Supabase
        const soalId = crypto.randomUUID()
        // Update ID soal di state lokal agar jawaban mahasiswa bisa match dengan soal_id Supabase
        q.id = soalId

        const { error: soalErr } = await supabase.from('soal').insert({
          id: soalId,
          tugas_id: newTask.id,
          type: q.type || 'multiple_choice',
          question_text: q.title || q.questionText || '',
          points: Number(q.points) || 10,
          order_index: i + 1,
        })

        if (soalErr) {
          console.warn('[Supabase DB] Error insert soal:', soalErr.message)
          continue
        }

        // Simpan Opsi Pilihan Ganda
        if (q.options && q.options.length > 0) {
          const letters = ['A', 'B', 'C', 'D', 'E']
          const opsiRows = q.options.map((optText, optIdx) => ({
            soal_id: soalId,
            option_letter: letters[optIdx] || String(optIdx + 1),
            option_text: optText,
            is_correct: q.answerKey ? optText.trim().toLowerCase() === q.answerKey.trim().toLowerCase() : optIdx === 0,
            order_index: optIdx + 1,
          }))
          await supabase.from('opsi_jawaban').insert(opsiRows)
        }

        // Simpan Kunci Jawaban Esai ke Supabase & ChromaDB
        if (q.type === 'essay' || q.type === 'short_answer' || (!q.options?.length && q.answerKey)) {
          const idKunci = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `key-${Date.now()}-${i}`
          await supabase.from('kunci_jawaban_essay').insert({
            id: idKunci,
            soal_id: soalId,
            answer_key: q.answerKey || '',
            rubric: q.rubric || [],
          })

          // Simpan ke ChromaDB Vector Store
          saveEssayKey({
            idKunci,
            idSoal: soalId,
            soal: q.title || '',
            kunciTeks: q.answerKey || '',
            rubrik: q.rubric || [],
          }).catch((err) => console.warn('[ChromaDB Sync] Sync vektor gagal:', err.message))
        }
      }
    } catch (err) {
      console.warn('[Supabase DB] Background task sync error:', err.message)
    }
  })()

  return newTask
}

function updateTask(classId, taskId, update) {
  const classItem = classes.value.find((item) => String(item.id) === String(classId))
  const task = classItem?.tasks?.find((item) => String(item.id) === String(taskId))
  if (!task) return null

  update(task)
  saveLocal()
  return task
}

/**
 * Simpan jawaban tugas mahasiswa ke Supabase (`jawaban_mahasiswa` & `detail_jawaban`).
 */
async function saveTaskSubmission(classId, taskId, submission) {
  const updatedTask = updateTask(classId, taskId, (task) => {
    task.submissions ||= []
    const email = submission.email.trim().toLowerCase()
    const existingIndex = task.submissions.findIndex(
      (item) => item.email.trim().toLowerCase() === email,
    )

    if (existingIndex === -1) task.submissions.push(submission)
    else task.submissions[existingIndex] = submission
  })

  // Sinkronisasi ke Supabase
  try {
    const { data: { user } } = await supabase.auth.getUser()
    const studentId = user?.id

    if (studentId) {
      const submissionId = submission.id || (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `sub-${Date.now()}`)
      
      const { data: subData, error: subErr } = await supabase
        .from('jawaban_mahasiswa')
        .upsert(
          {
            id: submissionId,
            tugas_id: taskId,
            student_id: studentId,
            status: submission.graded ? 'graded' : 'submitted',
            total_score: submission.score ?? null,
            submitted_at: new Date().toISOString(),
          },
          { onConflict: 'tugas_id,student_id' },
        )
        .select()
        .single()

      if (!subErr && subData && Array.isArray(submission.answers)) {
        for (const ans of submission.answers) {
          const detailRow = {
            submission_id: subData.id,
            soal_id: ans.questionId,
            jawaban_teks: ans.value || '',
            nilai_final: ans.score ?? null,
            teacher_feedback: ans.feedback || null,
          }

          if (ans.aiEvaluation) {
            if (typeof ans.aiEvaluation.similarity === 'number') {
              detailRow.similarity_score = ans.aiEvaluation.similarity
            }
            if (typeof ans.aiEvaluation.nilai_ai === 'number') {
              detailRow.nilai_ai = ans.aiEvaluation.nilai_ai
            }
            if (ans.aiEvaluation.evaluasi_rubrik) {
              detailRow.rubric_evaluation = ans.aiEvaluation.evaluasi_rubrik
            }
          }

          await supabase.from('detail_jawaban').insert(detailRow)
        }
      }
    }
  } catch (err) {
    console.warn('[Supabase DB] Error simpan jawaban:', err.message)
  }

  return updatedTask
}

function updateTaskSettings(classId, taskId, settings) {
  const updated = updateTask(classId, taskId, (task) => Object.assign(task, settings))
  
  // Update di Supabase
  supabase
    .from('tugas')
    .update({
      show_score: settings.showScore,
      show_correct_answers: settings.showCorrectAnswers,
    })
    .eq('id', taskId)
    .then()
    .catch((err) => console.warn('[Supabase DB] Update settings error:', err.message))

  return updated
}

async function updateSubmissionScore(classId, taskId, email, score) {
  const updated = updateTask(classId, taskId, (task) => {
    const submission = task.submissions?.find(
      (item) => item.email.trim().toLowerCase() === email.trim().toLowerCase(),
    )
    if (!submission) return

    submission.score = score
    submission.graded = true
  })

  // Sinkronisasi update nilai ke tabel `jawaban_mahasiswa` di Supabase
  try {
    const { data: profiles } = await supabase
      .from('profiles')
      .select('id')
      .eq('email', email.trim().toLowerCase())
      .single()

    if (profiles?.id) {
      await supabase
        .from('jawaban_mahasiswa')
        .update({
          total_score: score,
          status: 'graded',
          graded_at: new Date().toISOString(),
        })
        .eq('tugas_id', taskId)
        .eq('student_id', profiles.id)
    }
  } catch (err) {
    console.warn('[Supabase DB] Gagal update nilai jawaban_mahasiswa:', err.message)
  }

  return updated
}

async function joinClassByCode(email, code) {
  const cleanCode = (code || '').trim().toUpperCase()
  if (!cleanCode) return { status: 'not-found' }
  
  // 1. Cari di database Supabase terlebih dahulu
  try {
    const { data: dbClass, error: findErr } = await supabase
      .from('kelas')
      .select(`
        id,
        teacher_id,
        title,
        major,
        description,
        code,
        created_at,
        profiles:teacher_id (
          id,
          email,
          name
        )
      `)
      .eq('code', cleanCode)
      .maybeSingle()

    if (dbClass) {
      const { data: { user } } = await supabase.auth.getUser()
      if (user) {
        await supabase.from('anggota_kelas').upsert(
          {
            kelas_id: dbClass.id,
            student_id: user.id,
          },
          { onConflict: 'kelas_id,student_id' },
        )
      }

      // Pastikan kelas ada di state lokal
      let existing = classes.value.find((c) => String(c.id) === String(dbClass.id) || c.code?.toUpperCase() === cleanCode)
      if (!existing) {
        existing = {
          id: dbClass.id,
          teacherId: dbClass.teacher_id,
          teacherEmail: dbClass.profiles?.email || '',
          lecturer: dbClass.profiles?.name || 'Dosen',
          title: dbClass.title,
          major: dbClass.major || '',
          description: dbClass.description || '',
          code: dbClass.code,
          members: user ? [{ id: user.id, studentId: user.id, email: user.email, name: user.user_metadata?.name || 'Mahasiswa' }] : [],
          tasks: [],
        }
        classes.value.unshift(existing)
      } else if (user) {
        existing.members ||= []
        if (!existing.members.some((m) => m.studentId === user.id || m.email?.toLowerCase() === user.email?.toLowerCase())) {
          existing.members.push({
            id: user.id,
            studentId: user.id,
            email: user.email,
            name: user.user_metadata?.name || 'Mahasiswa',
          })
        }
      }
      
      const memberships = getMemberships(email)
      if (!memberships.some((m) => String(m) === String(dbClass.id) || String(m).toUpperCase() === cleanCode)) {
        localStorage.setItem(
          membershipStorageKey(email),
          JSON.stringify([...memberships, dbClass.id]),
        )
      }

      saveLocal()
      return { status: 'joined', classItem: existing }
    }
  } catch (err) {
    console.warn('[Supabase DB] Join query gagal, cek lokal:', err.message)
  }

  // 2. Cek di state lokal jika database tidak menemukan
  const classItem = classes.value.find((item) => item.code?.toUpperCase() === cleanCode)
  if (!classItem) return { status: 'not-found' }

  const memberships = getMemberships(email)
  if (memberships.some((id) => String(id) === String(classItem.id) || String(id).toUpperCase() === cleanCode)) {
    return { status: 'already-joined', classItem }
  }

  try {
    localStorage.setItem(
      membershipStorageKey(email),
      JSON.stringify([...memberships, classItem.id]),
    )
  } catch {
    return { status: 'storage-error' }
  }

  return { status: 'joined', classItem }
}

/**
 * Hapus kelas & hapus dari Supabase `kelas`.
 */
async function deleteClass(classId) {
  const strId = String(classId)
  classes.value = classes.value.filter((c) => String(c.id) !== strId)
  saveLocal()

  // Hapus di Supabase jika terautentikasi
  try {
    const { error } = await supabase.from('kelas').delete().eq('id', classId)
    if (error) {
      console.warn('[Supabase DB] Hapus kelas gagal:', error.message)
    }
  } catch (err) {
    console.warn('[Supabase DB] Hapus kelas gagal:', err.message)
  }
}

/**
 * Keluar dari kelas untuk mahasiswa & hapus dari `anggota_kelas`.
 */
async function leaveClass(email, classId) {
  const strId = String(classId)
  const memberships = getMemberships(email)
  const updatedMemberships = memberships.filter((id) => String(id) !== strId)

  try {
    localStorage.setItem(
      membershipStorageKey(email),
      JSON.stringify(updatedMemberships),
    )
  } catch {
    // ignore
  }

  const classItem = classes.value.find((c) => String(c.id) === strId)
  if (classItem && Array.isArray(classItem.members)) {
    classItem.members = classItem.members.filter((m) => m.email?.toLowerCase() !== email?.toLowerCase())
  }
  saveLocal()

  // Hapus dari Supabase jika terautentikasi
  try {
    const { data: { user } } = await supabase.auth.getUser()
    if (user) {
      const { error } = await supabase
        .from('anggota_kelas')
        .delete()
        .eq('kelas_id', classId)
        .eq('student_id', user.id)

      if (error) {
        console.warn('[Supabase DB] Keluar kelas gagal:', error.message)
      }
    }
  } catch (err) {
    console.warn('[Supabase DB] Keluar kelas gagal:', err.message)
  }

  return getClassesForStudent(email)
}

// Jalankan sync saat modul dimuat
syncClassesFromSupabase()

export {
  classes,
  isSyncing,
  addClass,
  addTaskToClass,
  deleteClass,
  leaveClass,
  getClassesForStudent,
  getClassesForTeacher,
  joinClassByCode,
  saveTaskSubmission,
  syncClassesFromSupabase,
  updateSubmissionScore,
  updateTaskSettings,
}
