// @vitest-environment happy-dom
// One tap to a way of learning: a topic card's Words half and a topic page each open the words straight in cards or a quiz.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { forgetSeen, markSeen } from '../../../lib/colloquial/seen'
import WordsView from '../words/WordsView'
import { TopicList, UnitList } from './Lists'

vi.mock('../../../lib/speech/speak', () => ({ speak: vi.fn(), prepare: vi.fn(), stop: vi.fn() }))
vi.mock('../../../lib/learner/record', () => ({ useRecord: () => ({ file: vi.fn() }), summaryQuery: () => ({ queryKey: ['summary'], queryFn: async () => [] }) }))

const topic = { lesson: 'lesson-01', title: 'Greetings', written: true, phrases: 14, words: 9 }
const unit = { unit: 'unit-01', title: 'First', written: true, lessons: [topic], cover: null, samples: [], words: 0 }
const dialect = { key: 'fusha', label: 'Fusha', where: 'Everywhere', units: [unit], countries: [], cities: [] }
const wrap = (ui) => render(<QueryClientProvider client={new QueryClient()}>{ui}</QueryClientProvider>)

beforeEach(() => { forgetSeen(); globalThis.scrollTo = vi.fn(); window.history.replaceState({}, '', '/colloq/fusha/unit-01') })
afterEach(cleanup)

describe('quick access', () => {
  it('a topic card opens its words straight in cards or a quiz', () => {
    const go = vi.fn()
    wrap(<TopicList dialect={dialect} unit={unit} go={go} />)
    fireEvent.click(screen.getByRole('button', { name: 'Quiz the words of Greetings' }))
    expect(go).toHaveBeenLastCalledWith({ dialect: 'fusha', unit: 'unit-01', at: 0, words: true, mode: 'quiz' })
    fireEvent.click(screen.getByRole('button', { name: 'Cards the words of Greetings' }))
    expect(go).toHaveBeenLastCalledWith({ dialect: 'fusha', unit: 'unit-01', at: 0, words: true, mode: 'cards' })
  })

  it('a word list opened with a mode starts in it, and the address keeps it', () => {
    const lesson = { lesson: 'lesson-01', title: 'T', written: true, phrases: [], vocabulary: ['qa', 'qb', 'qc', 'qd'].map((id) => ({ id, english: id, arabic: `ك${id}`, transliteration: id, category: 'zzz' })) }
    wrap(<WordsView unit={{ unit: 'unit-01', dialect_key: 'fusha', title: 'U', lessons: [lesson] }} at={0} start="cards" />)
    expect(screen.getByRole('group', { name: 'How to learn the words' }).querySelector('[aria-pressed=true]').textContent).toBe('Cards')
    expect(window.location.search + window.history.state?.view?.words).toMatch(/cards/)
  })

  it('a dialect page offers the way back to its last topic, and not to another dialect’s', () => {
    markSeen('fusha/unit-01/lesson-01')
    const other = { ...dialect, key: 'gulf', label: 'Gulf' }
    const { unmount } = wrap(<UnitList dialect={dialect} dialects={[dialect, other]} go={() => {}} />)
    expect(screen.getByRole('button', { name: /Continue where you left off/ })).toBeTruthy()
    unmount()
    wrap(<UnitList dialect={other} dialects={[dialect, other]} go={() => {}} />)
    expect(screen.queryByRole('button', { name: /Continue where you left off/ })).toBeNull()
  })
})
