export function formatErrorMessage(error) {
  if (typeof error === 'string') return error
  if (!error || typeof error !== 'object') return ''

  const parts = [error.message, error.error, error.details, error.hint].filter(
    (value) => typeof value === 'string' && value.trim(),
  )
  if (error.code) parts.push(`Kode: ${error.code}`)

  return [...new Set(parts)].join(' — ') || JSON.stringify(error)
}
