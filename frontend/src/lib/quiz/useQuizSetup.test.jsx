// @vitest-environment happy-dom
// The Quiz's set, until one is picked, is the learner's level's; answers filed mid-round that move the level must not
// swap it under the player, while a level picked by hand is followed at once.
import { afterEach, describe, expect, it } from 'vitest'
import { act, waitFor } from '@testing-library/react'

import { renderWithBackend } from '../../test/render'
import { useQuizSetup } from './useQuizSetup'
import { levelOf, RULES } from '../learner/learnerLevel'
import { useLearnerLevel } from '../learner/useLearnerLevel'
import { useRecord } from '../learner/record'
import { forgetDevice, writeDevice } from '../store/stored'
import CONFIG from '../../config/profile.json'

afterEach(() => {
  forgetDevice(CONFIG.storageKey)
  localStorage.clear()
})

const bankOf = (level) => levelOf(level)['quiz-bank']

describe('useQuizSetup, the level’s set', () => {
  it('holds while answers move the level, and follows a level picked by hand', async () => {
    writeDevice(CONFIG.storageKey, 'amina')
    let answers = RULES.minAnswers - 1
    const { result } = renderWithBackend(() => ({ setup: useQuizSetup(), level: useLearnerLevel(), record: useRecord() }), {
      routes: {
        'GET /progress/overview': () => ({ modules: [{ module: 'basics', attempts: answers, correct: answers, learnt: 0 }] }),
        'POST /progress/attempts': () => { answers += 1; return { earned: 1 } },
      },
    })
    act(() => result.current.level.choose('beginner'))
    await waitFor(() => expect(result.current.level.known).toBe(true))
    expect(result.current.setup.bankId).toBe(bankOf('beginner'))

    await act(() => result.current.record.file({ module: 'basics', item: 'al:kitab', correct: true }))
    await waitFor(() => expect(result.current.level.level).toBe('intermediate'))
    expect(result.current.setup.bankId).toBe(bankOf('beginner'))

    act(() => result.current.level.choose('advanced'))
    expect(result.current.setup.bankId).toBe(bankOf('advanced'))
  })
})
