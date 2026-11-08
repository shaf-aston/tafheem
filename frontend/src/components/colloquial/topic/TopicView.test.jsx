// @vitest-environment happy-dom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { scrollToEl } from '../../../lib/motion/scrollToEl'
import TopicView from './TopicView'

vi.mock('../../../lib/learner/record', () => ({ useRecord: () => ({ file: vi.fn() }) }))
vi.mock('../../../lib/motion/scrollToEl', async (original) => ({ ...(await original()), scrollToEl: vi.fn() }))

const say = (n) => ({ arabic: `عربي${n}`, transliteration: `arabee${n}`, english: `phrase ${n}`, image: null })
const word = (n) => ({ id: `w${n}`, arabic: `كلمة${n}`, transliteration: `kalima${n}`, english: `word ${n}`, group: 'things' })
const lesson = (extra = {}) => ({
  lesson: 'lesson-01', title: 'Greetings', written: true,
  phrases: [say(1), say(2), say(3)],
  vocabulary: [word(1), word(2)],
  dialogue: [{ speaker: 'A', arabic: 'أهلا', transliteration: 'ahlan', english: 'Hello' }],
  de_book: [{ pair: say(4), response: say(5) }],
  exercises: [{ id: 'x1', type: 'choose', prompt: 'Pick one', answer: 'a', accepted: ['a'], options: ['a', 'b', 'c'] }],
  culture: 'People greet warmly.',
  ...extra,
})
const unit = (l) => ({ dialect_key: 'egyptian', unit: 'unit-01', title: 'First', lessons: [l], words: [] })
const draw = (l) => render(<QueryClientProvider client={new QueryClient()}><TopicView unit={unit(l)} at={0} /></QueryClientProvider>)

beforeEach(() => { globalThis.scrollTo = vi.fn() })
afterEach(cleanup)

describe('TopicView', () => {
  it('says its own name and lays out the scene in order: words, hearing it, matching, practice, culture', () => {
    draw(lesson())
    expect(screen.getByRole('heading', { level: 2, name: 'Greetings' })).toBeTruthy()
    const heads = screen.getAllByRole('heading', { level: 3 }).map((h) => h.textContent)
    expect(heads).toEqual(['2 words for this topic', 'Hear it said', 'Ask and answer', 'Practice'])
    expect(screen.getByText('People greet warmly.')).toBeTruthy()
  })

  it('"Practice ↓" takes the learner to the practice', () => {
    draw(lesson())
    fireEvent.click(screen.getByRole('button', { name: 'Practice ↓' }))
    expect(scrollToEl).toHaveBeenCalledTimes(1)
    expect(scrollToEl.mock.calls[0][0].textContent).toContain('Pick one')
  })

  it('a long word list shows a few and the rest a tap away', () => {
    draw(lesson({ vocabulary: Array.from({ length: 9 }, (_, i) => word(i + 1)) }))
    expect(screen.queryByText('word 9')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Show all 9 words' }))
    expect(screen.getByText('word 9')).toBeTruthy()
    expect(screen.queryByRole('button', { name: /Show all 9/ })).toBeNull()
  })

  it('a topic with no words has no word section', () => {
    draw(lesson({ vocabulary: [] }))
    expect(screen.queryByText(/words for this topic/)).toBeNull()
  })

  it('a phrase opens in a sheet that closes again', () => {
    draw(lesson())
    fireEvent.click(screen.getAllByRole('button', { name: /phrase 1/ })[0])
    const sheet = screen.getByRole('dialog')
    expect(sheet.textContent).toContain('phrase 1')
    fireEvent.click(screen.getByRole('button', { name: 'Close' }))
    expect(screen.queryByRole('dialog')).toBeNull()
  })
})
