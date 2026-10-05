export function isScannedTask(task) {
  return (
    task?.isScanned === true ||
    task?.submissions?.some((submission) => submission.isScanned === true) === true
  )
}

export function canStudentViewTask(task, studentId, email) {
  if (!isScannedTask(task)) return true

  const normalizedEmail = email?.trim().toLowerCase()
  return Boolean(
    task.submissions?.some((submission) => {
      if (!submission.isScanned) return false
      if (studentId && submission.studentId) return submission.studentId === studentId
      return Boolean(
        normalizedEmail &&
          submission.email?.trim().toLowerCase() === normalizedEmail,
      )
    }),
  )
}

export function canTeacherViewTask(task) {
  return !isScannedTask(task)
}
