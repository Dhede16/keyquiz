import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import { resolveMultipleChoiceAnswerKey } from './quizAnswerKey.js'

describe('resolveMultipleChoiceAnswerKey', () => {
  it('resolves an AI answer letter to its option text', () => {
    const options = [
      { huruf: 'A', teks: 'Jawaban salah' },
      { huruf: 'B', teks: 'Jawaban benar' },
    ]

    assert.equal(resolveMultipleChoiceAnswerKey(options, 'B'), 'Jawaban benar')
  })

  it('matches answer letters without depending on letter case or surrounding spaces', () => {
    assert.equal(resolveMultipleChoiceAnswerKey([{ huruf: 'b', teks: 'Opsi B' }], ' B '), 'Opsi B')
  })

  it('preserves an answer key that is already option text', () => {
    assert.equal(resolveMultipleChoiceAnswerKey([{ huruf: 'A', teks: 'Opsi A' }], 'Opsi A'), 'Opsi A')
  })
})
