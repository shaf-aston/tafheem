// @vitest-environment happy-dom
// "Your Arabic": free to change until the answers settle it, then shown with the answers that set it. A guest's is
// always their own choice (guests share one record, so it is never read as theirs).
import { afterEach, describe, expect, it } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import LevelSetting from '../components/level/LevelSetting'
import { LEVEL_COPY, LEVEL_KEY, RULES } from '../lib/learnerLevel'
import { forgetDevice, readRaw, writeDevice } from '../lib/stored'
import CONFIG from '../config/profile.json'

const overview = (modules) => ({ modules, attempts: 0, correct: 0, learnt: 0, streak: 0 })
const row = (module, attempts, correct) => ({ module, attempts, correct, learnt: 0, lastAt: '2026-10-23T00:00:00Z' })

afterEach(() => {
  forgetDevice(CONFIG.storageKey)
  localStorage.clear()
})

describe('Your Arabic', () => {
  it('lets a guest choose, and says the answers will confirm it once logged in', () => {
    renderScreen(<LevelSetting />)
    fireEvent.click(screen.getByRole('button', { name: 'Intermediate' }))
    expect(readRaw(LEVEL_KEY)).toBe('intermediate')
    expect(screen.getByText(new RegExp(LEVEL_COPY.guest))).toBeTruthy()
  })

  it('stays open to change while too few answers are in', async () => {
    writeDevice(CONFIG.storageKey, 'amina')
    renderScreen(<LevelSetting />, {
      routes: { 'GET /progress/overview': overview([row('basics', RULES.minAnswers - 1, 0)]) },
    })
    fireEvent.click(await screen.findByRole('button', { name: 'Advanced' }))
    expect(readRaw(LEVEL_KEY)).toBe('advanced')
    expect(screen.queryByText(new RegExp(LEVEL_COPY.guest))).toBeNull()
  })

  it('locks once settled, naming the level and the answers that set it', async () => {
    writeDevice(CONFIG.storageKey, 'amina')
    renderScreen(<LevelSetting />, { routes: { 'GET /progress/overview': overview([row('basics', 40, 36)]) } })
    const reason = await screen.findByText(/90% right over 40 Basics answers/)
    expect(reason.textContent).toMatch(/^Intermediate · Set by your answers/)
    expect(screen.queryByRole('group', { name: LEVEL_COPY.label })).toBeNull()
  })
})
