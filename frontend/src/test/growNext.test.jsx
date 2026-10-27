// @vitest-environment happy-dom
// Home's "Next in Grow": one step picked from the record (lib/grow/suggest.js), down to the lesson, one tap to start.
// The journey is one per page, so these run in order: a first visit, then places walked.
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { act, fireEvent, screen, waitFor, within } from '@testing-library/react'

import { renderScreen } from './render'
import HomePanel from '../components/home/HomePanel'
import { visit } from '../lib/nav/journey'
import { LEVEL_KEY } from '../lib/learner/learnerLevel'
import { writeRaw } from '../lib/store/stored'
import knobs from '../config/home.json'
import { OFFERED } from '../components/home/GrowNext'

const NEXT = { name: knobs.copy['next-label'] }
const used = (module, attempts) => ({
  'GET /progress/overview': {
    modules: [{ module, attempts, correct: attempts, learnt: 0, lastAt: new Date().toISOString() }],
    attempts, correct: attempts, learnt: 0, streak: 1,
  },
  'GET /progress/summary': { items: [] },
})

beforeEach(() => localStorage.clear())

describe('Next in Grow', () => {
  it('on a new visit with a record, offers what was being studied above the level picker', async () => {
    renderScreen(<HomePanel accent="var(--primary)" onGo={vi.fn()} />, { routes: used('jawhara', 6) })
    const next = await screen.findByRole('region', NEXT)
    await within(next).findByText(/^Jawhara › /)
    const fork = screen.getByRole('region', { name: knobs.copy['fork-label'] })
    expect(next.compareDocumentPosition(fork) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it('stays hidden on a first visit, and when it is where you stopped', async () => {
    writeRaw(LEVEL_KEY, 'beginner')
    renderScreen(<HomePanel accent="var(--primary)" onGo={vi.fn()} />)
    await waitFor(() => expect(screen.queryByRole('region', NEXT)).toBeNull())
    act(() => { visit('grow', 'basics/lesson') })
    await screen.findByRole('button', { name: /Continue/ })
    expect(screen.queryByRole('region', NEXT)).toBeNull()
  })

  it('with no record, offers the world the level starts from', async () => {
    writeRaw(LEVEL_KEY, 'beginner')
    renderScreen(<HomePanel accent="var(--primary)" onGo={vi.fn()} />)
    act(() => { visit('dict', 'كتب') })
    const next = await screen.findByRole('region', NEXT)
    await waitFor(() => expect(next.textContent).toContain('Basics'))
    expect(next.textContent).toContain(knobs.copy['next-level'])
  })

  it('holds its place, a quiet bar with no button, while the record is read, once a visit has offered a step', async () => {
    writeRaw(OFFERED, 'on')
    renderScreen(<HomePanel accent="var(--primary)" onGo={vi.fn()} />, { routes: used('jawhara', 6) })
    const next = screen.getByRole('region', NEXT)
    expect(within(next).queryByRole('button')).toBeNull()
    await within(next).findByRole('button')
  })

  it('holds nothing on a first visit, so nothing collapses if there is no step', () => {
    renderScreen(<HomePanel accent="var(--primary)" onGo={vi.fn()} />, { routes: used('jawhara', 6) })
    expect(screen.queryByRole('region', NEXT)).toBeNull()
  })

  it('offers the book being studied, down to its next lesson, and one tap starts it', async () => {
    const onGo = vi.fn()
    renderScreen(<HomePanel accent="var(--primary)" onGo={onGo} />, { routes: used('jawhara', 6) })
    const next = await screen.findByRole('region', NEXT)
    await within(next).findByText('Praise, and why the poem was written')
    expect(next.textContent).toContain('Jawhara › Opening: why, and what every Muslim must know')
    expect(next.textContent).toContain(knobs.copy['next-recent'])
    fireEvent.click(within(next).getByRole('button'))
    expect(onGo).toHaveBeenCalledWith('grow', 'jawhara/jaw-open/jaw-open-why')
  })

  it('a book with questions due offers its review', async () => {
    const due = ['nabi-state', 'aqib-means', 'name', 'hope'].map((id) => ({
      item: `jaw-open-why/${id}`, attempts: 1, wrong: 0, avgMs: 1, due: true, known: false, dueAt: '2026-01-01', words: [],
    }))
    const onGo = vi.fn()
    renderScreen(<HomePanel accent="var(--primary)" onGo={onGo} />, { routes: { ...used('jawhara', 6), 'GET /progress/summary': { items: due } } })
    const next = await screen.findByRole('region', NEXT)
    await within(next).findByText('4 questions to review')
    fireEvent.click(within(next).getByRole('button'))
    expect(onGo).toHaveBeenCalledWith('grow', 'jawhara/review')
  })
})
