// @vitest-environment happy-dom
// A newcomer's first visit, through the whole app: Home's "Start the basics" is handed to Grow, which opens the lesson
// at once (not Grow's home, as a reopened tab would). Its own file, so no other test's journey is left behind.
import { describe, expect, it } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import App from '../App'
import home from '../home.json'

describe('first visit', () => {
  it('hands a newcomer from Home straight into the Basics lesson', async () => {
    renderScreen(<App />, { routes: { 'GET /progress/summary': { items: [] } } })
    fireEvent.click(await screen.findByRole('button', { name: new RegExp(home.copy['new-go']) }))
    expect(await screen.findByText('means “the”', {}, { timeout: 3000 })).toBeTruthy()
  })
})
