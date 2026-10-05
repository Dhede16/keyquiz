export function normalizeQuizPoints(questions) {
  if (questions.length === 0) return []

  const pointsPerQuestion = Math.floor(100 / questions.length)
  const extraPoints = 100 % questions.length

  return questions.map((question, index) => ({
    ...question,
    points: pointsPerQuestion + (index < extraPoints ? 1 : 0),
  }))
}

export function setQuizQuestionPoints(questions, questionIndex, points) {
  const questionCount = questions.length
  const maxPoints = 100 - (questionCount - 1)

  if (
    !Number.isInteger(points) ||
    points < 1 ||
    points > maxPoints ||
    (questionCount === 1 && points !== 100) ||
    !Number.isInteger(questionIndex) ||
    questionIndex < 0 ||
    questionIndex >= questionCount
  ) {
    throw new RangeError('Bobot harus berupa angka bulat dan menyisakan minimal 1 poin per soal.')
  }

  const remainingQuestions = questions.filter((_, index) => index !== questionIndex)
  const pointsPerRemainingQuestion = remainingQuestions.length
    ? Math.floor((100 - points) / remainingQuestions.length)
    : 0
  const extraRemainingPoints = remainingQuestions.length
    ? (100 - points) % remainingQuestions.length
    : 0
  let remainingIndex = 0

  return questions.map((question, index) =>
    index === questionIndex
      ? { ...question, points }
      : {
          ...remainingQuestions[remainingIndex],
          points:
            pointsPerRemainingQuestion +
            (remainingIndex++ < extraRemainingPoints ? 1 : 0),
        },
  )
}

export function hasQuizPointsTotalOf100(questions) {
  if (questions.length === 0) return false

  return (
    questions.every((question) => {
      const points = Number(question.points)
      return Number.isInteger(points) && points > 0
    }) &&
    questions.reduce((total, question) => total + Number(question.points), 0) === 100
  )
}

export function getQuizPointsTotal(questions) {
  return (
    questions.reduce((total, question) => {
      const points = Number(question.points) || 0
      return total + Math.round(points * 100)
    }, 0) / 100
  )
}
