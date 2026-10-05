export function resolveMultipleChoiceAnswerKey(options, answerKey) {
  if (!Array.isArray(options) || typeof answerKey !== 'string') return answerKey || ''

  const normalizedKey = answerKey.trim().toLocaleLowerCase()
  const matchingOption = options.find(
    (option) => String(option?.huruf ?? '').trim().toLocaleLowerCase() === normalizedKey,
  )

  return matchingOption?.teks ?? answerKey
}
