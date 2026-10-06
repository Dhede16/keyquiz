import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import { formatErrorMessage } from './errorMessage.js'

describe('formatErrorMessage', () => {
  it('preserves useful fields from Supabase error objects', () => {
    assert.equal(
      formatErrorMessage({
        message: 'new row violates row-level security policy',
        code: '42501',
        details: 'The request was rejected.',
      }),
      'new row violates row-level security policy — The request was rejected. — Kode: 42501',
    )
  })

  it('formats regular errors and falls back for unexpected values', () => {
    assert.equal(formatErrorMessage(new Error('Network error')), 'Network error')
    assert.equal(formatErrorMessage({ statusCode: 404 }), '{"statusCode":404}')
    assert.equal(formatErrorMessage(null), '')
  })
})
