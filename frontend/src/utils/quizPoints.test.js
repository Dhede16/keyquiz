import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import {
  getQuizPointsTotal,
  hasQuizPointsTotalOf100,
  normalizeQuizPoints,
  setQuizQuestionPoints,
} from './quizPoints.js'

describe('normalizeQuizPoints', () => {
  it('assigns balanced whole-number points after adding a question', () => {
    const questions = normalizeQuizPoints([
      { id: 1, points: 50 },
      { id: 2, points: 50 },
      { id: 3, points: 10 },
    ])

    assert.deepEqual(questions.map((question) => question.points), [34, 33, 33])
    assert.equal(getQuizPointsTotal(questions), 100)
    assert.equal(hasQuizPointsTotalOf100(questions), true)
  })

  it('assigns equal points when the total divides evenly after removing a question', () => {
    const questions = normalizeQuizPoints([
      { id: 1, points: 99 },
      { id: 2, points: 1 },
    ])

    assert.deepEqual(questions.map((question) => question.points), [50, 50])
    assert.equal(getQuizPointsTotal(questions), 100)
  })

  it('keeps every question within one point of the others and validates only integers', () => {
    const questions = normalizeQuizPoints(
      Array.from({ length: 6 }, (_, id) => ({ id, points: id + 1 })),
    )

    assert.deepEqual(questions.map((question) => question.points), [17, 17, 17, 17, 16, 16])
    assert.equal(hasQuizPointsTotalOf100(questions), true)
    assert.equal(
      hasQuizPointsTotalOf100([
        { points: 33.34 },
        { points: 33.33 },
        { points: 33.33 },
      ]),
      false,
    )
  })

  it('preserves a manually selected weight and balances the remaining points', () => {
    const questions = setQuizQuestionPoints(
      [
        { id: 1, points: 34 },
        { id: 2, points: 33 },
        { id: 3, points: 33 },
      ],
      1,
      50,
    )

    assert.deepEqual(questions.map((question) => question.points), [25, 50, 25])
    assert.equal(getQuizPointsTotal(questions), 100)
    assert.equal(hasQuizPointsTotalOf100(questions), true)
  })

  it('rejects manual weights that cannot keep all question weights positive integers', () => {
    assert.throws(
      () => setQuizQuestionPoints([{ points: 50 }, { points: 50 }], 0, 100),
      RangeError,
    )
    assert.throws(() => setQuizQuestionPoints([{ points: 100 }], 0, 50), RangeError)
  })
})
