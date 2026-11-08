// @vitest-environment happy-dom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { forgetSeen } from '../../lib/colloquial/seen'
import ColloquialPanel from './ColloquialPanel'

vi.mock('../../lib/learner/record', () => ({ useRecord: () => ({ file: vi.fn() }), summaryQuery: (m) => ({ queryKey: ['summary', m], queryFn: async () => [] }) }))

const topic = (n, extra = {}) => ({ lesson: `lesson-0${n}`, title: `Topic title ${n}`, written: true, phrases: 2, words: 0, ...extra })
const catalogue = {
  dialects: [
    { key: 'egyptian', label: 'Egyptian', arabic: 'المصري', where: 'Cairo', gloss: 'Cairo speech', countries: [], cities: [],
      units: [{ unit: 'unit-01', title: 'First Conversations', written: true, lessons: [topic(1), topic(2)], cover: null, samples: [], words: 0 }] },
    { key: 'gulf', label: 'Gulf', arabic: 'الخليجي', where: 'The Gulf', gloss: '', countries: [], cities: [], units: [] },
  ],
}
const phrase = (n) => ({ arabic: `عربي${n}`, transliteration: `arabee${n}`, english: `phrase ${n}`, image: null })
const lessonBody = (n) => ({
  ...topic(n), phrases: [phrase(1), phrase(2)], vocabulary: [],
  dialogue: [{ speaker: 'A', arabic: 'أهلا', transliteration: 'ahlan', english: 'Hello' }],
  de_book: [{ pair: phrase(3), response: phrase(4) }],
  exercises: [{ id: `x${n}`, type: 'choose', prompt: 'Pick one', answer: 'a', accepted: ['a'], options: ['a', 'b', 'c'] }],
  culture: `Culture ${n}`,
})
const unitBody = { dialect_key: 'egyptian', unit: 'unit-01', title: 'First Conversations', lessons: [lessonBody(1), lessonBody(2)] }

function mount(props = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  client.setQueryData(['colloquial'], catalogue)
  client.setQueryData(['colloquial-unit', 'egyptian', 'unit-01'], unitBody)
  const onVisit = vi.fn()
  render(<QueryClientProvider client={client}><ColloquialPanel incoming={null} arrival={0} onVisit={onVisit} {...props} /></QueryClientProvider>)
  return { onVisit }
}

beforeEach(() => { globalThis.scrollTo = vi.fn(); forgetSeen() })
afterEach(cleanup)

const trail = () => screen.getByRole('navigation', { name: 'Where you are' })

describe('ColloquialPanel', () => {
  it('opens on the dialects, and each step down is a place on the journey', () => {
    const { onVisit } = mount()
    expect(screen.getByRole('button', { name: /Egyptian/ })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /Egyptian/ }))
    expect(onVisit).toHaveBeenLastCalledWith('egyptian')
    fireEvent.click(screen.getByRole('button', { name: /First Conversations/ }))
    expect(onVisit).toHaveBeenLastCalledWith('egyptian/unit-01')
    expect(trail().textContent).toContain('Unit 1')
  })

  it('a topic opens as a scene, and the trail climbs back up', () => {
    const { onVisit } = mount({ incoming: 'egyptian/unit-01', arrival: 1 })
    fireEvent.click(screen.getByRole('button', { name: /Topic title 1/ }))
    expect(onVisit).toHaveBeenLastCalledWith('egyptian/unit-01/lesson-01')
    expect(screen.getByRole('heading', { level: 2, name: 'Topic title 1' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Dialects' }))
    expect(onVisit).toHaveBeenLastCalledWith(null)
    expect(screen.getByRole('button', { name: /Gulf/ })).toBeTruthy()
  })

  it('a pasted link lands on its topic, and the next topic is one tap on', () => {
    const { onVisit } = mount({ incoming: 'egyptian/unit-01/lesson-01', arrival: 1 })
    expect(screen.getByRole('heading', { level: 2, name: 'Topic title 1' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /Next topic: Topic title 2/ }))
    expect(onVisit).toHaveBeenLastCalledWith('egyptian/unit-01/lesson-02')
    expect(screen.queryByRole('button', { name: /Next topic/ })).toBeNull()
  })

  it('a stale link opens the start and says so, until the learner moves', () => {
    mount({ incoming: 'egyptian/unit-99', arrival: 1 })
    expect(screen.getByRole('status').textContent).toContain('did not match a lesson')
    fireEvent.click(screen.getByRole('button', { name: /Egyptian/ }))
    expect(screen.queryByText(/did not match a lesson/)).toBeNull()
  })

  it('no note for a bare address', () => {
    mount()
    expect(screen.queryByText(/did not match a lesson/)).toBeNull()
  })

  it('the topics a learner opened come back as a Continue card', () => {
    mount({ incoming: 'egyptian/unit-01/lesson-02', arrival: 1 })
    fireEvent.click(screen.getByRole('button', { name: 'Dialects' }))
    expect(screen.getByRole('button', { name: /Continue where you left off/ }).textContent).toContain('Topic title 2')
  })
})
