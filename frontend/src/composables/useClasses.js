import { ref } from 'vue'
import { classes as initialClasses } from '@/data/classes.js'
import { supabase } from '@/services/supabase.js'
import { saveEssayKey } from '@/services/api.js'
import { canStudentViewTask } from '@/utils/scannedTaskAccess.js'
import { hasQuizPointsTotalOf100 } from '@/utils/quizPoints.js'

const CLASSES_STORAGE_KEY = 'keyquiz:classes'
const classes = ref(loadInitialClasses())
const isSyncing = ref(false)

function loadInitialClasses() {
  try {
    const stored = JSON.parse(localStorage.getItem(CLASSES_STORAGE_KEY))
    return Array.isArray(stored) && stored.length > 0
      ? stored.map(({ archiveFolders, ...classItem }) => classItem)
      : [...initialClasses]
  } catch {
    return [...initialClasses]
  }
}

function saveLocal() {
  try {
    localStorage.setItem(
      CLASSES_STORAGE_KEY,
      JSON.stringify(classes.value.map(({ archiveFolders, ...classItem }) => classItem)),
    )
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
  }).map((classItem) => ({
    ...classItem,
    tasks: (classItem.tasks || []).filter((task) =>
      canStudentViewTask(task, studentId, email),
    ),
  }))
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
            name,
            avatar_url
          )
        ),
        scan_archive_folders (
          id,
          name,
          created_at,
          scan_archives (
            id,
            task_id,
            student_id,
            quiz_title,
            original_file_path,
            questions,
            created_at,
            profiles:student_id (
              id,
              email,
              name
            )
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
              name,
              avatar_url
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
              teacher_feedback,
              yakin_scan
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
          avatarUrl: ak.profiles?.avatar_url || '',
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
            avatarUrl: jm.profiles?.avatar_url || '',
            score: jm.total_score,
            graded: jm.status === 'graded',
            isScanned: jm.is_scanned,
            maxScore: formattedQuestions.reduce((sum, question) => sum + question.points, 0),
            submittedAt: jm.submitted_at,
            answers: (jm.detail_jawaban || []).map((dj) => {
              const question = formattedQuestions.find((item) => item.id === dj.soal_id)
              const similarity = dj.similarity_score ?? dj.nilai_ai
              const aiScore =
                similarity != null && question && jm.is_scanned
                  ? Number(similarity)
                  : similarity != null && question
                    ? Math.round((Number(similarity) / 100) * (Number(question.points) || 10))
                  : null

              return {
                id: dj.id,
                questionId: dj.soal_id,
                value: dj.jawaban_teks,
                score: dj.nilai_final ?? aiScore,
                feedback: dj.teacher_feedback,
                isCertain: dj.yakin_scan,
                rubricEvaluation: dj.rubric_evaluation,
                aiScore,
                aiEvaluation:
                  similarity == null || jm.is_scanned
                    ? null
                    : {
                        similarity: Number(similarity),
                        nilai_ai: Number(similarity),
                      },
              }
            }),
          }))

          return {
            id: t.id,
            title: t.title,
            createdAt: t.created_at,
            isScanned: (t.jawaban_mahasiswa || []).some((submission) => submission.is_scanned),
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
          archiveFolders: (c.scan_archive_folders || []).map((folder) => ({
            id: folder.id,
            name: folder.name,
            createdAt: folder.created_at,
            archives: (folder.scan_archives || []).map((archive) => ({
              id: archive.id,
              taskId: archive.task_id,
              studentId: archive.student_id,
              studentEmail: archive.profiles?.email || '',
              studentName: archive.profiles?.name || 'Mahasiswa',
              title: archive.quiz_title,
              originalFilePath: archive.original_file_path,
              questions: archive.questions || [],
              createdAt: archive.created_at,
            })),
          })),
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

  if (
    Array.isArray(task.questions) &&
    task.questions.length > 0 &&
    !hasQuizPointsTotalOf100(task.questions)
  ) {
    throw new Error('Total bobot seluruh soal harus tepat 100 poin.')
  }

  const taskId = task.id || crypto.randomUUID()
  const newTask = {
    showScore: true,
    showCorrectAnswers: false,
    submissions: [],
    ...task,
    id: taskId,
    createdAt: task.createdAt || new Date().toISOString(),
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
          points: Number(q.points),
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

async function updateTaskInClass(classId, taskId, update) {
  const classItem = classes.value.find((item) => String(item.id) === String(classId))
  const task = classItem?.tasks?.find((item) => String(item.id) === String(taskId))
  if (!task) throw new Error('Tugas yang akan diedit tidak ditemukan.')

  const questions = (update.questions || []).map((question) => ({ ...question }))
  if (questions.length === 0 || !hasQuizPointsTotalOf100(questions)) {
    throw new Error('Total bobot seluruh soal harus tepat 100 poin.')
  }

  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError) throw new Error(`Gagal memeriksa sesi dosen: ${authError.message}`)
  if (user) {
    const { data: dbQuestions, error: questionsError } = await supabase
      .from('soal')
      .select('id')
      .eq('tugas_id', taskId)
    if (questionsError) throw new Error(`Gagal memuat soal tersimpan: ${questionsError.message}`)

    const existingIds = new Set((dbQuestions || []).map((question) => String(question.id)))
    const retainedIds = new Set(
      questions.filter((question) => existingIds.has(String(question.id))).map((question) => String(question.id)),
    )
    const removedIds = [...existingIds].filter((id) => !retainedIds.has(id))

    if (removedIds.length > 0) {
      const { data: answeredQuestions, error: answersError } = await supabase
        .from('detail_jawaban')
        .select('soal_id')
        .in('soal_id', removedIds)
        .limit(1)
      if (answersError) throw new Error(`Gagal memeriksa jawaban mahasiswa: ${answersError.message}`)
      if (answeredQuestions?.length) {
        throw new Error('Soal yang sudah dijawab mahasiswa tidak dapat dihapus agar jawaban mereka tetap tersimpan.')
      }
    }

    const { data: savedTask, error: taskError } = await supabase
      .from('tugas')
      .update({
        title: update.title,
        description: update.description || null,
        deadline: update.dueAt || null,
        show_score: update.showScore ?? true,
        show_correct_answers: update.showCorrectAnswers ?? false,
      })
      .eq('id', taskId)
      .select('id')
      .single()
    if (taskError) throw new Error(`Gagal memperbarui tugas: ${taskError.message}`)
    if (!savedTask) throw new Error('Tugas tidak ditemukan atau tidak dapat diedit.')

    for (let index = 0; index < questions.length; index++) {
      const question = questions[index]
      const questionId = existingIds.has(String(question.id)) ? String(question.id) : crypto.randomUUID()
      question.id = questionId
      const questionData = {
        type: question.type === 'multiple_choice' ? 'multiple_choice' : 'short_answer',
        question_text: question.title,
        points: Number(question.points),
        order_index: index + 1,
      }

      const questionResult = existingIds.has(questionId)
        ? await supabase.from('soal').update(questionData).eq('id', questionId).eq('tugas_id', taskId)
        : await supabase.from('soal').insert({ id: questionId, tugas_id: taskId, ...questionData })
      if (questionResult.error) {
        throw new Error(`Gagal memperbarui soal ${index + 1}: ${questionResult.error.message}`)
      }

      const { data: currentOptions, error: optionsQueryError } = await supabase
        .from('opsi_jawaban')
        .select('id')
        .eq('soal_id', questionId)
        .order('order_index')
      if (optionsQueryError) throw new Error(`Gagal memuat opsi soal ${index + 1}: ${optionsQueryError.message}`)

      const options = question.type === 'multiple_choice' ? question.options || [] : []
      const letters = ['A', 'B', 'C', 'D', 'E']
      for (let optionIndex = 0; optionIndex < Math.max(currentOptions.length, options.length); optionIndex++) {
        const existingOption = currentOptions[optionIndex]
        const optionText = options[optionIndex]
        if (existingOption && optionText !== undefined) {
          const { error } = await supabase
            .from('opsi_jawaban')
            .update({
              option_letter: letters[optionIndex] || String(optionIndex + 1),
              option_text: optionText,
              is_correct: Boolean(question.answerKey) &&
                optionText.trim().toLowerCase() === question.answerKey.trim().toLowerCase(),
              order_index: optionIndex + 1,
            })
            .eq('id', existingOption.id)
          if (error) throw new Error(`Gagal memperbarui opsi soal ${index + 1}: ${error.message}`)
        } else if (optionText !== undefined) {
          const { error } = await supabase.from('opsi_jawaban').insert({
            soal_id: questionId,
            option_letter: letters[optionIndex] || String(optionIndex + 1),
            option_text: optionText,
            is_correct: Boolean(question.answerKey) &&
              optionText.trim().toLowerCase() === question.answerKey.trim().toLowerCase(),
            order_index: optionIndex + 1,
          })
          if (error) throw new Error(`Gagal menambahkan opsi soal ${index + 1}: ${error.message}`)
        } else if (existingOption) {
          const { error } = await supabase.from('opsi_jawaban').delete().eq('id', existingOption.id)
          if (error) throw new Error(`Gagal menghapus opsi soal ${index + 1}: ${error.message}`)
        }
      }

      if (question.type !== 'multiple_choice') {
        const { error } = await supabase
          .from('kunci_jawaban_essay')
          .upsert(
            {
              soal_id: questionId,
              answer_key: question.answerKey || '',
              rubric: question.rubric || [],
            },
            { onConflict: 'soal_id' },
          )
        if (error) throw new Error(`Gagal memperbarui kunci esai soal ${index + 1}: ${error.message}`)

        saveEssayKey({
          idKunci: `kunci-${questionId}`,
          idSoal: questionId,
          soal: question.title || '',
          kunciTeks: question.answerKey || '',
          rubrik: question.rubric || [],
        }).catch((error) => console.warn('[ChromaDB Sync] Sinkronisasi kunci esai gagal:', error.message))
      } else {
        const { error } = await supabase.from('kunci_jawaban_essay').delete().eq('soal_id', questionId)
        if (error) throw new Error(`Gagal menghapus kunci esai soal ${index + 1}: ${error.message}`)
      }
    }

    if (removedIds.length > 0) {
      const { error } = await supabase.from('soal').delete().in('id', removedIds)
      if (error) throw new Error(`Gagal menghapus soal yang belum dijawab: ${error.message}`)
    }
  }

  Object.assign(task, update, { questions })
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
            nilai_final: ans.aiEvaluation ? null : (ans.score ?? null),
            teacher_feedback: ans.feedback || null,
          }

          if (ans.aiEvaluation) {
            if (typeof ans.aiEvaluation.similarity === 'number') {
              detailRow.similarity_score = ans.aiEvaluation.similarity
            }
            if (typeof ans.aiEvaluation.nilai_ai === 'number') {
              detailRow.nilai_ai = ans.aiEvaluation.nilai_ai
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

async function saveScannedSubmission(
  classId,
  studentId,
  questions,
  quizTitle,
  { originalFile, folderId = null, folderName = '' } = {},
) {
  const classItem = classes.value.find((item) => String(item.id) === String(classId))
  if (!classItem) throw new Error('Kelas yang dipilih tidak ditemukan.')
  if (!Array.isArray(questions) || questions.length === 0) {
    throw new Error('Tidak ada soal hasil scan untuk dikirim.')
  }
  if (
    !originalFile ||
    !['image/jpeg', 'image/png', 'image/webp'].includes(originalFile.type) ||
    originalFile.size > 10 * 1024 * 1024
  ) {
    throw new Error('Foto scan wajib berupa JPG, PNG, atau WEBP dengan ukuran maksimal 10 MB.')
  }
  const usesExistingFolder = Boolean(folderId && folderId !== 'new')
  if (!usesExistingFolder && !folderName.trim()) {
    throw new Error('Nama folder arsip wajib diisi.')
  }
  if (!usesExistingFolder && folderName.trim().length > 100) {
    throw new Error('Nama folder arsip maksimal 100 karakter.')
  }
  for (const [index, question] of questions.entries()) {
    if (
      !question ||
      !question.title?.trim() ||
      !Array.isArray(question.options) ||
      question.options.some(
        (option) => !option?.value || !option.label?.trim(),
      )
    ) {
      throw new Error(`Format opsi soal ${index + 1} tidak valid.`)
    }
    const optionValues = question.options.map((option) => option.value)
    if (
      !question.title?.trim() ||
      question.options.length < 2 ||
      new Set(optionValues).size !== optionValues.length ||
      !optionValues.includes(question.answerKey) ||
      (question.selectedOption && !optionValues.includes(question.selectedOption)) ||
      !Number.isFinite(Number(question.points)) ||
      Number(question.points) < 0 ||
      !Number.isFinite(Number(question.score)) ||
      Number(question.score) < 0 ||
      Number(question.score) > Number(question.points) ||
      !Number.isFinite(Number(question.aiScore)) ||
      Number(question.aiScore) < 0 ||
      Number(question.aiScore) > Number(question.points)
    ) {
      throw new Error(`Periksa kembali soal ${index + 1}, opsi, kunci jawaban, dan nilainya.`)
    }
  }
  const totalPoints =
    Math.round(questions.reduce((sum, question) => sum + Number(question.points), 0) * 100) / 100
  if (totalPoints !== 100) {
    throw new Error('Total bobot seluruh soal harus tepat 100 poin.')
  }

  const { data: { user }, error: userError } = await supabase.auth.getUser()
  if (userError) throw new Error(`Gagal memeriksa akun dosen: ${userError.message}`)
  if (!user || classItem.teacherId !== user.id) {
    throw new Error('Hanya dosen pengampu kelas yang dapat mengirim hasil scan.')
  }

  const { data: membership, error: membershipError } = await supabase
    .from('anggota_kelas')
    .select('student_id')
    .eq('kelas_id', classItem.id)
    .eq('student_id', studentId)
    .maybeSingle()

  if (membershipError) throw new Error(`Gagal memeriksa mahasiswa kelas: ${membershipError.message}`)
  if (!membership) throw new Error('Mahasiswa yang dipilih bukan anggota kelas ini.')

  const { data: student, error: studentError } = await supabase
    .from('profiles')
    .select('id, email, name')
    .eq('id', studentId)
    .single()
  if (studentError) throw new Error(`Data mahasiswa tidak ditemukan: ${studentError.message}`)

  const cleanQuizTitle = quizTitle.trim()
  if (!cleanQuizTitle) throw new Error('Nama kuis tidak boleh kosong.')

  const taskId = crypto.randomUUID()
  const task = {
    id: taskId,
    title: cleanQuizTitle,
    description: 'Hasil scan lembar pilihan ganda yang telah dikoreksi dosen.',
    status: 'published',
    showScore: true,
    showCorrectAnswers: true,
    isScanned: true,
    date: new Date().toLocaleDateString('id-ID'),
    questions: [],
    submissions: [],
  }

  const savedQuestionData = []
  let taskCreated = false
  let archiveFolder = null
  let archiveFolderCreated = false
  let archiveFilePath = null
  let archiveImageUploaded = false
  try {
    if (folderId && folderId !== 'new') {
      const { data, error } = await supabase
        .from('scan_archive_folders')
        .select('id, name, created_at')
        .eq('id', folderId)
        .eq('class_id', classItem.id)
        .single()
      if (error) throw new Error(`Folder arsip tidak dapat ditemukan: ${error.message}`)
      archiveFolder = data
    } else {
      const { data, error } = await supabase
        .from('scan_archive_folders')
        .insert({
          class_id: classItem.id,
          created_by: user.id,
          name: folderName.trim(),
        })
        .select('id, name, created_at')
        .single()
      if (error) {
        const message = error.code === '23505'
          ? 'Nama folder tersebut sudah digunakan di kelas ini.'
          : ['PGRST205', '42P01'].includes(error.code)
            ? 'Skema arsip belum tersedia di Supabase. Jalankan database/migrations/20261006_scanned_sheet_archives.sql di SQL Editor, lalu coba lagi.'
            : error.message
        throw new Error(`Gagal membuat folder arsip: ${message}`)
      }
      archiveFolder = data
      archiveFolderCreated = true
    }

    const extensionByType = {
      'image/jpeg': 'jpg',
      'image/png': 'png',
      'image/webp': 'webp',
    }
    archiveFilePath = `${classItem.id}/${archiveFolder.id}/${crypto.randomUUID()}.${extensionByType[originalFile.type]}`
    const { error: uploadError } = await supabase.storage
      .from('scan-archives')
      .upload(archiveFilePath, originalFile, { contentType: originalFile.type, upsert: false })
    if (uploadError) throw new Error(`Gagal menyimpan foto scan ke arsip: ${uploadError.message}`)
    archiveImageUploaded = true

    const { error: taskError } = await supabase.from('tugas').insert({
      id: taskId,
      kelas_id: classItem.id,
      title: task.title,
      description: task.description,
      status: task.status,
      show_score: true,
      show_correct_answers: true,
    })
    if (taskError) throw new Error(`Gagal menyimpan tugas scan: ${taskError.message}`)
    taskCreated = true

    for (let index = 0; index < questions.length; index++) {
      const question = questions[index]
      const questionId = crypto.randomUUID()
      const { error: questionError } = await supabase.from('soal').insert({
        id: questionId,
        tugas_id: taskId,
        type: 'multiple_choice',
        question_text: question.title,
        points: Number(question.points),
        order_index: index + 1,
      })
      if (questionError) throw new Error(`Gagal menyimpan soal ${index + 1}: ${questionError.message}`)

      const options = question.options.map((option, optionIndex) => ({
        soal_id: questionId,
        option_letter: option.value,
        option_text: option.label,
        is_correct: option.value === question.answerKey,
        order_index: optionIndex + 1,
      }))
      const { data: savedOptions, error: optionsError } = await supabase
        .from('opsi_jawaban')
        .insert(options)
        .select('id, option_letter, option_text')
      if (optionsError) throw new Error(`Gagal menyimpan opsi soal ${index + 1}: ${optionsError.message}`)

      task.questions.push({
        id: questionId,
        title: question.title,
        type: 'multiple_choice',
        points: Number(question.points),
        options: question.options.map((option) => option.label),
        answerKey: question.options.find((option) => option.value === question.answerKey)?.label || '',
      })
      savedQuestionData.push({ id: questionId, options: savedOptions })
    }

    const totalScore = questions.reduce((sum, question) => sum + Number(question.score || 0), 0)
    const { data: submission, error: submissionError } = await supabase
      .from('jawaban_mahasiswa')
      .insert({
        tugas_id: taskId,
        student_id: student.id,
        status: 'graded',
        total_score: totalScore,
        is_scanned: true,
        submitted_at: new Date().toISOString(),
        graded_at: new Date().toISOString(),
      })
      .select('id')
      .single()
    if (submissionError) throw new Error(`Gagal menyimpan hasil mahasiswa: ${submissionError.message}`)

    const details = questions.map((question, index) => ({
      submission_id: submission.id,
      soal_id: savedQuestionData[index].id,
      opsi_jawaban_id:
        savedQuestionData[index].options.find((option) => option.option_letter === question.selectedOption)?.id || null,
      jawaban_teks:
        question.options.find((option) => option.value === question.selectedOption)?.label || '',
      nilai_final: Number(question.score || 0),
      nilai_ai: Number(question.aiScore || 0),
      yakin_scan: question.isCertain,
    }))
    const { error: detailsError } = await supabase.from('detail_jawaban').insert(details)
    if (detailsError) throw new Error(`Gagal menyimpan detail hasil scan: ${detailsError.message}`)

    const archivedQuestions = questions.map((question) => ({
      title: question.title,
      options: question.options,
      selectedOption: question.selectedOption,
      answerKey: question.answerKey,
      aiScore: Number(question.aiScore),
      points: Number(question.points),
      score: Number(question.score),
      isCertain: Boolean(question.isCertain),
    }))
    const { data: archivedScan, error: archiveError } = await supabase
      .from('scan_archives')
      .insert({
        class_id: classItem.id,
        folder_id: archiveFolder.id,
        task_id: taskId,
        student_id: student.id,
        quiz_title: cleanQuizTitle,
        original_file_path: archiveFilePath,
        questions: archivedQuestions,
      })
      .select('id, created_at')
      .single()
    if (archiveError) throw new Error(`Gagal menyimpan arsip hasil scan: ${archiveError.message}`)

    task.submissions.push({
      id: submission.id,
      studentId: student.id,
      email: student.email,
      name: student.name,
      score: totalScore,
      maxScore: questions.reduce((sum, question) => sum + Number(question.points), 0),
      graded: true,
      isScanned: true,
      submittedAt: new Date().toISOString(),
      answers: questions.map((question, index) => ({
        questionId: savedQuestionData[index].id,
        value: question.options.find((option) => option.value === question.selectedOption)?.label || '',
        score: Number(question.score || 0),
        isCertain: question.isCertain,
      })),
    })
    classItem.tasks ||= []
    classItem.tasks.unshift(task)
    classItem.archiveFolders ||= []
    let localFolder = classItem.archiveFolders.find((folder) => folder.id === archiveFolder.id)
    if (!localFolder) {
      localFolder = {
        id: archiveFolder.id,
        name: archiveFolder.name,
        createdAt: archiveFolder.created_at,
        archives: [],
      }
      classItem.archiveFolders.unshift(localFolder)
    }
    localFolder.archives ||= []
    localFolder.archives.unshift({
      id: archivedScan.id,
      taskId,
      studentId: student.id,
      studentEmail: student.email,
      studentName: student.name,
      title: cleanQuizTitle,
      originalFilePath: archiveFilePath,
      questions: archivedQuestions,
      createdAt: archivedScan.created_at,
    })
    task.archiveFolderId = archiveFolder.id
    saveLocal()
    return task
  } catch (error) {
    const cleanupErrors = []
    let taskCleanupSucceeded = !taskCreated
    if (taskCreated) {
      try {
        const { error: cleanupError } = await supabase.from('tugas').delete().eq('id', taskId)
        if (cleanupError) throw cleanupError
        taskCleanupSucceeded = true
      } catch (cleanupError) {
        cleanupErrors.push(`data tugas: ${cleanupError.message}`)
      }
    }
    if (!taskCleanupSucceeded) {
      cleanupErrors.push('foto dan folder arsip terkait dipertahankan agar tidak merusak data yang masih tersimpan')
    } else if (archiveFilePath && archiveImageUploaded) {
      try {
        const { error: cleanupError } = await supabase.storage
          .from('scan-archives')
          .remove([archiveFilePath])
        if (cleanupError) cleanupErrors.push(`foto arsip: ${cleanupError.message}`)
      } catch (cleanupError) {
        cleanupErrors.push(`foto arsip: ${cleanupError.message}`)
      }
    }
    if (taskCleanupSucceeded && archiveFolderCreated && archiveFolder) {
      try {
        const { error: cleanupError } = await supabase
          .from('scan_archive_folders')
          .delete()
          .eq('id', archiveFolder.id)
        if (cleanupError) cleanupErrors.push(`folder arsip: ${cleanupError.message}`)
      } catch (cleanupError) {
        cleanupErrors.push(`folder arsip: ${cleanupError.message}`)
      }
    }
    if (cleanupErrors.length) {
      throw new Error(`${error.message} Pembersihan data parsial gagal (${cleanupErrors.join('; ')}).`)
    }
    throw error
  }
}

async function getScannedArchiveImageUrl(path) {
  if (!path) throw new Error('Lokasi foto arsip tidak tersedia.')

  const { data, error } = await supabase.storage
    .from('scan-archives')
    .createSignedUrl(path, 600)
  if (error) throw new Error(`Gagal membuka foto arsip: ${error.message}`)
  return data.signedUrl
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

async function updateSubmissionScore(classId, taskId, email, score, questionScores = null) {
  const updated = updateTask(classId, taskId, (task) => {
    const submission = task.submissions?.find(
      (item) => item.email.trim().toLowerCase() === email.trim().toLowerCase(),
    )
    if (!submission) return

    submission.score = score
    submission.graded = true

    if (questionScores && Array.isArray(submission.answers)) {
      submission.answers.forEach((ans) => {
        if (questionScores[ans.questionId] !== undefined) {
          ans.score = Number(questionScores[ans.questionId])
        }
      })
    }
  })

  // Sinkronisasi update nilai ke tabel `jawaban_mahasiswa` & `detail_jawaban` di Supabase
  try {
    const { data: profiles } = await supabase
      .from('profiles')
      .select('id')
      .eq('email', email.trim().toLowerCase())
      .single()

    if (profiles?.id) {
      const { data: jm } = await supabase
        .from('jawaban_mahasiswa')
        .update({
          total_score: score,
          status: 'graded',
          graded_at: new Date().toISOString(),
        })
        .eq('tugas_id', taskId)
        .eq('student_id', profiles.id)
        .select('id')
        .maybeSingle()

      if (jm?.id && questionScores) {
        for (const [soalId, qScore] of Object.entries(questionScores)) {
          await supabase
            .from('detail_jawaban')
            .update({
              nilai_final: Number(qScore),
            })
            .eq('submission_id', jm.id)
            .eq('soal_id', soalId)
        }
      }
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
  getScannedArchiveImageUrl,
  joinClassByCode,
  saveTaskSubmission,
  saveScannedSubmission,
  syncClassesFromSupabase,
  updateSubmissionScore,
  updateTaskInClass,
  updateTaskSettings,
}
