// @vitest-environment happy-dom
// A newcomer's first visit, through the whole app: Home asks a few questions, and Start opens the level they come to
// (not Grow's home, as a reopened tab would). Its own file, so no other test's journey is left behind.
import { describe, expect, it } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import App from '../App'
import config from '../config/onboarding.json'

const { copy } = config
const press = async (name) => fireEvent.click(await screen.findByRole('button', { name }))

describe('first visit', () => {
  it('takes a beginner from the questions straight into the Basics lesson', async () => {
    renderScreen(<App />, { routes: { 'GET /progress/summary': { items: [] } } })
    fireEvent.click(await screen.findByRole('checkbox', { name: /Understand the Qur/ }))
    await press(copy.continue)
    fireEvent.click(await screen.findByRole('radio', { name: /Not yet/ }))
    await press(copy.continue)
    // Language, memorised, minutes: one pick each.
    for (const label of ['English', 'Not much yet', '10 min']) {
      fireEvent.click(await screen.findByRole('radio', { name: new RegExp(label) }))
      await press(copy.continue)
    }
    await press(copy['ready-start'])
    expect(await screen.findByText('means “the”', {}, { timeout: 3000 })).toBeTruthy()
  })
})
