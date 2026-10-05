import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import { getClassStatisticsStudents } from './classStatistics.js'

describe('getClassStatisticsStudents', () => {
  it('includes scanned submission scores in student statistics', () => {
    const [student] = getClassStatisticsStudents(
      [{ id: 'student-1', name: 'Mahasiswa', email: 'student@example.com' }],
      [
        {
          id: 'quiz-1',
          title: 'Kuis',
          submissions: [{ email: 'student@example.com', score: 80 }],
        },
        {
          id: 'scan-1',
          title: 'Hasil Scan',
          isScanned: true,
          submissions: [{ email: 'student@example.com', score: 100, isScanned: true }],
        },
      ],
    )

    assert.deepEqual(
      student.quizScores.map(({ title, score }) => ({ title, score })),
      [
        { title: 'Kuis', score: 80 },
        { title: 'Hasil Scan', score: 100 },
      ],
    )
    assert.equal(student.average, 90)
  })
})
