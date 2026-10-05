import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import { canTeacherViewTask } from './scannedTaskAccess.js'

describe('canTeacherViewTask', () => {
  it('hides scanned tasks from the teacher class view', () => {
    assert.equal(canTeacherViewTask({ isScanned: true }), false)
    assert.equal(
      canTeacherViewTask({
        submissions: [{ isScanned: true }],
      }),
      false,
    )
  })

  it('keeps non-scanned tasks visible to the teacher', () => {
    assert.equal(canTeacherViewTask({ isScanned: false }), true)
    assert.equal(canTeacherViewTask({}), true)
  })
})
