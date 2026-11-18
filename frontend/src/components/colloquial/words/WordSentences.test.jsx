// @vitest-environment happy-dom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import WordsView from './WordsView'

vi.mock('../../../lib/speech/speak', () => ({ speak: vi.fn(), prepare: vi.fn(), stop: vi.fn() }))
vi.mock('../../../lib/learner/record', () => ({ useRecord: () => ({ file: vi.fn() }), summaryQuery: () => ({ queryKey: ['summary'], queryFn: async () => [] }) }))

// Not words a drawing knows, so Browse is the plain list (no picture board).
const word = (id) => ({ id, english: id, arabic: `ك${id}`, transliteration: id, category: 'zzz' })
const sentence = (slot, english) => ({ slot, english, arabic: `جملة ${slot}`, transliteration: `jumla ${slot}`, uses: [] })
const lesson = (sentences) => ({ lesson: 'lesson-01', title: 'Little Words', written: true, phrases: [], vocabulary: ['qa', 'qb', 'qc'].map(word), sentences })
const draw = (l) => render(<QueryClientProvider client={new QueryClient()}><WordsView unit={{ unit: 'unit-20', dialect_key: 'fusha', title: 'U', lessons: [l] }} at={0} /></QueryClientProvider>)

beforeEach(() => { globalThis.scrollTo = vi.fn(); window.history.replaceState({}, '', '/colloq/fusha/unit-20/lesson-01') })
afterEach(cleanup)

describe('a word topic: its words, then the same words in sentences', () => {
  it('shows the words first and its sentences after them, each a tile that opens and says it', () => {
    const { container } = draw(lesson([sentence('one', 'Where is the book?'), sentence('two', 'It is under the table.')]))
    const heading = screen.getByRole('heading', { name: 'The words in use' })
    const firstWord = screen.getByText('كqa')
    expect(firstWord.compareDocumentPosition(heading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()   // words first
    expect(screen.getByText('Where is the book?')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /It is under the table\./ }))
    expect(screen.getByRole('dialog')).toBeTruthy()
    expect(container.ownerDocument.body.textContent).toContain('2 / 2')
  })

  it('shows no sentence section for a topic that has none', () => {
    draw(lesson([]))
    expect(screen.queryByRole('heading', { name: 'The words in use' })).toBeNull()
  })
})
