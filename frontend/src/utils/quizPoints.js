export function normalizeQuizPoints(questions) {
  if (questions.length === 0) return []

  const weights = questions.map((question) => {
    const points = Number(question.points)
    return Number.isFinite(points) && points > 0 ? points : 1
  })
  const weightTotal = weights.reduce((total, points) => total + points, 0)
  const exactCents = weights.map((points) => (points / weightTotal) * 10000)
  const cents = exactCents.map(Math.floor)
  let centsRemaining = 10000 - cents.reduce((total, points) => total + points, 0)

  const remainderOrder = exactCents
    .map((points, index) => ({ index, remainder: points - cents[index] }))
    .sort((a, b) => b.remainder - a.remainder)

  for (let index = 0; centsRemaining > 0; index++, centsRemaining--) {
    cents[remainderOrder[index].index]++
  }

  return questions.map((question, index) => ({
    ...question,
    points: cents[index] / 100,
  }))
}

export function hasQuizPointsTotalOf100(questions) {
  if (questions.length === 0) return false

  return (
    questions.every((question) => {
      const points = Number(question.points)
      return Number.isFinite(points) && points > 0
    }) &&
    questions.reduce((total, question) => total + Math.round(Number(question.points) * 100), 0) ===
      10000
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
