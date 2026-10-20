// @vitest-environment happy-dom
// The whole app opens with no backend: the shell draws its header, a tab, and
// the offline banner, and moving to another tab shows that tab.
import { describe, expect, it } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import App from '../App'
import home from '../home.json'

describe('app shell', () => {
  it('opens on Home when nothing is saved', async () => {
    renderScreen(<App />)
    expect(await screen.findByRole('heading', { name: home.copy['title-first'] })).toBeTruthy()
  })

  it('opens, says the backend is down, and switches tab', async () => {
    renderScreen(<App />)
    expect(await screen.findByRole('button', { name: 'Open the launcher' })).toBeTruthy()
    expect(await screen.findByText(home.copy['offline-title'], {}, { timeout: 3000 })).toBeTruthy()
    fireEvent.click(screen.getAllByRole('tab', { name: /Quiz/ })[0])
    expect(await screen.findByRole('heading', { name: 'Quiz' }, { timeout: 3000 })).toBeTruthy()
  })
})
