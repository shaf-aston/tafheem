// @vitest-environment happy-dom
// Grow's Fiqh world on the real book file: from the parts to Purity's lessons, into the Wudu lesson, and through its
// questions — the reason shows after an answer, and every answer is filed under the book's module.
import { describe, expect, it } from 'vitest'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'

import { renderScreen } from './render'
import GrowPanel from '../components/GrowPanel'

const click = (name) => fireEvent.click(screen.getByRole('button', { name }))
const option = (name) => screen.getByRole('radio', { name })

describe('fiqh', () => {
  it('goes world → part → lesson, and plays its questions', async () => {
    const filed = []
    const visits = []
    renderScreen(<GrowPanel incoming="fiqh" onVisit={(value) => visits.push(value)} />, {
      routes: {
        'GET /progress/summary': { items: [] },
        'POST /progress/attempts': (config) => { filed.push(JSON.parse(config.data)); return { earned: 1 } },
      },
    })

    // The parts: Purity has lessons, Prayer is still coming.
    fireEvent.click(await screen.findByRole('button', { name: /Purity/ }))
    expect(visits.at(-1)).toBe('fiqh/tahara')
    const lessons = screen.getAllByRole('listitem')
    expect(within(lessons[0]).getByText('Wudu: fard, sunnah, mustahabb')).toBeTruthy()

    fireEvent.click(within(lessons[0]).getByRole('button'))
    expect(visits.at(-1)).toBe('fiqh/tahara/wudu')

    // Teach, then "which are fard?": pick the four, Check, and the reason is said.
    expect(screen.getByText('The fard of wudu')).toBeTruthy()
    click('Continue')
    for (const name of ['Wash the face', 'Wash the arms, elbows included', 'Wipe the head', 'Wash the feet, ankles included']) click(name)
    click('Check')
    expect(screen.getByRole('status').textContent).toMatch(/^Right! The fard are the four in the ayah/)
    await waitFor(() => expect(filed.at(-1)).toMatchObject({ module: 'quduri', item: 'wudu/which-fard', correct: true }))

    // Teach, then the gap: a wrong word is marked and comes back at the end.
    click('Continue')
    click('Continue')
    fireEvent.click(option('اللحية'))
    click('Check')
    expect(screen.getByRole('status').textContent).toMatch(/The forelock .* It comes back at the end\./)
    await waitFor(() => expect(filed.at(-1)).toMatchObject({ item: 'wudu/head-gap', correct: false }))
    expect(option('الناصية').dataset.mark).toBe('right')

    // Two teach cards, then sort: Check waits until every row has a group.
    click('Continue')
    click('Continue')
    click('Continue')
    const check = screen.getByRole('button', { name: 'Check' })
    const rows = screen.getAllByRole('radiogroup')
    const answer = { 'Wash the face': 'Fard', 'Say Bismillah': 'Sunnah', 'Make the intention': 'Mustahabb', 'Wipe the forelock': 'Fard',
      'Use the siwak': 'Sunnah', 'Wipe the whole head': 'Mustahabb', 'Wash each limb three times': 'Sunnah' }
    rows.forEach((row, i) => {
      expect(check.disabled).toBe(true)
      fireEvent.click(within(row).getByRole('radio', { name: answer[row.getAttribute('aria-label')] }))
      if (i < rows.length - 1) expect(screen.getByRole('button', { name: 'Check' }).disabled).toBe(true)
    })
    click('Check')
    await waitFor(() => expect(filed.at(-1)).toMatchObject({ item: 'wudu/sort', correct: true }))

    // Order: tap the four in the ayah's order.
    click('Continue')
    for (const step of ['Wash the face', 'Wash the arms', 'Wipe the head', 'Wash the feet']) click(step)
    click('Check')
    await waitFor(() => expect(filed.at(-1)).toMatchObject({ item: 'wudu/order', correct: true }))
  })

  it('falls back to the part for a lesson the book does not have', async () => {
    renderScreen(<GrowPanel incoming="fiqh/tahara/nothing" />, { routes: { 'GET /progress/summary': { items: [] } } })
    expect(await screen.findByText('Wudu: fard, sunnah, mustahabb')).toBeTruthy()
  })
})
