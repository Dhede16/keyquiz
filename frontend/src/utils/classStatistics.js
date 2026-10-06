export function getClassStatisticsStudents(members, tasks) {
  return members.map((member) => {
    const studentEmail = member.email.toLowerCase()
    const quizScores = tasks.map((task) => {
      const submission = task.submissions?.find(
        (item) => item.email?.toLowerCase() === studentEmail,
      )
      return {
        id: task.id,
        title: task.title,
        score: submission && submission.score != null ? Number(submission.score) : null,
      }
    })
    const completedScores = quizScores
      .filter((quiz) => quiz.score !== null && quiz.score !== undefined)
      .map((quiz) => Number(quiz.score))

    return {
      id: member.id || member.studentId,
      name: member.name,
      email: member.email,
      avatarUrl: member.avatarUrl || '',
      average:
        completedScores.length > 0
          ? Math.round(
              completedScores.reduce((total, score) => total + score, 0) / completedScores.length,
            )
          : 0,
      quizScores,
    }
  })
}
