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
  it('goes world → area → part → lesson, and plays its questions', async () => {
    const filed = []
    const visits = []
    renderScreen(<GrowPanel incoming="fiqh" onVisit={(value) => visits.push(value)} />, {
      routes: {
        'GET /progress/summary': { items: [] },
        'POST /progress/attempts': (config) => { filed.push(JSON.parse(config.data)); return { earned: 1 } },
      },
    })

    // The areas, then Worship's parts, then Purity's lessons; Purity's back button returns to Worship.
    fireEvent.click(await screen.findByRole('button', { name: /^العبادات Worship/ }))
    expect(visits.at(-1)).toBe('fiqh/worship')
    fireEvent.click(screen.getByRole('button', { name: /Purity/ }))
    expect(visits.at(-1)).toBe('fiqh/tahara')
    expect(screen.getByRole('button', { name: 'Back to Worship' })).toBeTruthy()
    // The part's first unit is headed on the path; the ruling words open it, then wudu.
    expect(screen.getByRole('heading', { name: 'Wudu' })).toBeTruthy()
    const lessons = screen.getAllByRole('listitem').filter((item) => item.querySelector('button'))
    expect(within(lessons[0]).getByText('The ruling words')).toBeTruthy()
    expect(within(lessons[1]).getByText('Wudu: fard, sunnah, mustahabb')).toBeTruthy()

    fireEvent.click(within(lessons[1]).getByRole('button'))
    expect(visits.at(-1)).toBe('fiqh/tahara/wudu')

    // The part's cards arrive in their own file; then teach, "how many?", then "which are fard?": pick the four, Check,
    // and the reason is said.
    expect(await screen.findByText('The fard of wudu')).toBeTruthy()
    click('Continue')
    fireEvent.click(option('Four'))
    click('Check')
    await waitFor(() => expect(filed.at(-1)).toMatchObject({ item: 'wudu/fard-count', correct: true }))
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
    const answer = { 'Wipe the forelock': 'Fard', 'Use the siwak': 'Sunnah', 'Wash each limb three times': 'Sunnah',
      'Wipe the whole head': 'Mustahabb', 'Start with the right': 'Mustahabb' }
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

  it('still shows and plays the lessons when the record cannot be read', async () => {
    renderScreen(<GrowPanel incoming="fiqh/tahara" />, { routes: { 'GET /progress/summary': () => { throw new Error('down') } } })
    expect(await screen.findByText(/Your progress could not be loaded/, {}, { timeout: 4000 })).toBeTruthy()
    expect(screen.getByText('Wudu: fard, sunnah, mustahabb')).toBeTruthy()
  })

  it('leads Grow home with the book last studied, one tap from its next lesson', async () => {
    localStorage.setItem('grow-last-book', 'fiqh')
    const visits = []
    renderScreen(<GrowPanel incoming="" onVisit={(value) => visits.push(value)} />, { routes: { 'GET /progress/summary': { items: [] } } })
    expect(await screen.findByText('Continue · Fiqh')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    expect(visits.at(-1)).toMatch(/^fiqh\/tahara\//)
    localStorage.removeItem('grow-last-book')
  })

  it('opens on Grow home with the unfinished lesson to resume, not inside it', async () => {
    const visits = []
    renderScreen(<GrowPanel incoming="fiqh/tahara/wudu" onVisit={(value) => visits.push(value)} />, { routes: { 'GET /progress/summary': { items: [] } } })
    expect(await screen.findByText('Unfinished lesson')).toBeTruthy()
    expect(screen.queryByRole('progressbar', { name: 'Lesson progress' })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Resume' }))
    expect(visits.at(-1)).toBe('fiqh/tahara/wudu')
  })

  it('falls back to the part for a lesson the book does not have', async () => {
    renderScreen(<GrowPanel incoming="fiqh/tahara/nothing" />, { routes: { 'GET /progress/summary': { items: [] } } })
    fireEvent.click(await screen.findByRole('button', { name: 'Resume' }))
    expect(await screen.findByText('Wudu: fard, sunnah, mustahabb')).toBeTruthy()
  })

  it('finds a term in the book\'s glossary and opens the lesson that teaches it', async () => {
    const visits = []
    renderScreen(<GrowPanel incoming="fiqh" onVisit={(value) => visits.push(value)} />, { routes: { 'GET /progress/summary': { items: [] } } })
    fireEvent.click(await screen.findByText(/^Glossary · \d+ terms$/))
    fireEvent.change(screen.getByRole('searchbox', { name: 'Find a term' }), { target: { value: 'nisab' } })
    expect(screen.getByText(/the least amount of wealth on which zakat is due/)).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /^Lesson: / }))
    expect(visits.at(-1)).toBe('fiqh/zakah/zakah-who')
  })
})
