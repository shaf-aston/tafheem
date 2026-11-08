// @vitest-environment happy-dom
// The profile and Home's progress column read calm first: this week, then understanding, then the level and the rest.
import { beforeEach, describe, expect, it } from 'vitest'
import { screen, within } from '@testing-library/react'

import { renderScreen } from './render'
import ProfileView from '../components/profile/ProfileView'
import StatsRail from '../components/home/StatsRail'
import ProfileDialog from '../components/profile/ProfileDialog'
import { dayKey } from '../lib/learner/week'

const today = new Date().toISOString()
const ROUTES = {
  'GET /progress/account': { name: 'amina', joined: today, answers: 42, public: true },
  'GET /progress/overview': {
    modules: [{ module: 'quiz', attempts: 42, correct: 30, learnt: 1, lastAt: today }],
    attempts: 42, correct: 30, learnt: 1, streak: 2, days: [dayKey(new Date())],
  },
  'GET /progress/summary': { items: [
    { item: 'a', attempts: 4, wrong: 0, known: true, words: [] },
    { item: 'b', attempts: 2, wrong: 1, known: false, words: [] },
  ] },
  'GET /progress/rewards': { xp: 120, xpToday: 10, level: 2, into: 20, need: 100, streak: 2 },
  'GET /progress/leaderboard': { rows: [{ name: 'amina', learnt: 1, answers: 42, rank: 1 }], you: null },
}

// Each element follows the one before it on the page.
const inOrder = (...nodes) => nodes.every((node, i) =>
  i === 0 || nodes[i - 1].compareDocumentPosition(node) & Node.DOCUMENT_POSITION_FOLLOWING)

beforeEach(() => localStorage.clear())

describe('calm progress', () => {
  it('puts this week on top of the profile, then understanding, then the level and the rankings', async () => {
    renderScreen(<ProfileView name="amina" />, { routes: ROUTES })
    const week = screen.getByRole('region', { name: 'This week' })
    expect(await within(week).findByText('42')).toBeTruthy()
    expect(within(week).getByText('Words met').nextSibling.textContent).toBe('2')
    expect(within(week).getByText('Now known').nextSibling.textContent).toBe('1')
    // The server lists today alone as answered in: one filled dot, today marked.
    const days = await within(week).findAllByRole('listitem')
    expect(days).toHaveLength(7)
    expect(days.filter((day) => day.className.includes('week-studied')).length).toBe(1)
    expect(days.filter((day) => day.getAttribute('aria-current') === 'date')).toHaveLength(1)

    const understanding = screen.getByRole('region', { name: 'How much you understand' })
    const level = await screen.findByText(/^Lv 2 ·/)
    const ranking = await screen.findByText('Global ranking: words learnt')
    expect(inOrder(week, understanding, level, ranking)).toBe(true)
  })

  it('keeps that order in Home’s progress column', async () => {
    renderScreen(<StatsRail name="amina" />, { routes: ROUTES })
    const week = screen.getByRole('region', { name: 'This week' })
    const understanding = screen.getByRole('region', { name: 'How much you understand' })
    const level = await screen.findByText(/^Lv 2 ·/)
    const streak = screen.getByText('Streak')
    expect(inOrder(week, understanding, level, streak)).toBe(true)
  })

  it('shows a guest this device’s own week and understanding over the log-in', async () => {
    renderScreen(<ProfileDialog onClose={() => {}} />, { routes: ROUTES })
    const week = screen.getByRole('region', { name: 'This week' })
    expect(await within(week).findByText('42')).toBeTruthy()
    expect(inOrder(week, screen.getByRole('region', { name: 'How much you understand' }), screen.getByText('Username'))).toBe(true)
  })
})
