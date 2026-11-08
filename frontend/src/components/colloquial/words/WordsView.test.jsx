// @vitest-environment happy-dom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import spine from '../../../../../backend/data/colloquial/spine.json'
import WordsView from './WordsView'

vi.mock('../../../lib/learner/record', () => ({ useRecord: () => ({ file: vi.fn() }), summaryQuery: () => ({ queryKey: ['summary'], queryFn: async () => [] }) }))

const word = (id) => ({ id, english: id, arabic: `ك${id}`, transliteration: id, category: 'things' })
const topic = (ids) => ({ lesson: 'lesson-01', title: 'A topic', written: true, phrases: [], vocabulary: ids.map(word) })
const unit = (lesson) => ({ unit: 'unit-23', dialect_key: 'fusha', title: 'U', lessons: [lesson] })
const body = spine.units.flatMap((u) => u.lessons).find((l) => l.title === 'The Body, Head to Toe').words

const draw = (lesson) => render(<QueryClientProvider client={new QueryClient()}><WordsView unit={unit(lesson)} at={0} /></QueryClientProvider>)
const on = () => screen.getByRole('group', { name: 'How to learn the words' }).querySelector('[aria-pressed=true]').textContent

beforeEach(() => { globalThis.scrollTo = vi.fn(); window.history.replaceState({}, '', '/colloq/fusha/unit-23/lesson-01/words') })
afterEach(cleanup)

describe('WordsView: where a topic opens', () => {
  it('on its diagram when the words have one, with Browse a tap away', () => {
    draw(topic(body))
    expect(on()).toBe('Picture')
    fireEvent.click(screen.getByRole('button', { name: 'Browse' }))
    expect(on()).toBe('Browse')
  })

  it('on Browse when the words have no drawing', () => {
    draw(topic(['apple', 'bread', 'rice']))
    expect(on()).toBe('Browse')
    expect(screen.queryByRole('button', { name: 'Picture' })).toBeNull()
  })

  it('keeps a choice across a reload: Browse picked over a diagram stays Browse', () => {
    const first = draw(topic(body))
    fireEvent.click(screen.getByRole('button', { name: 'Browse' }))
    first.unmount()
    draw(topic(body))
    expect(on()).toBe('Browse')
  })

  it('a link asking for a mode a topic lacks opens on its own start', () => {
    window.history.replaceState({ view: { words: 'picture' } }, '', '/colloq/fusha/unit-23/lesson-01/words')
    draw(topic(['apple', 'bread', 'rice']))
    expect(on()).toBe('Browse')
  })

  it('the board and the Explore/Test step are kept across a reload and in a link', () => {
    const first = draw(topic(body))
    fireEvent.click(screen.getByRole('button', { name: 'Hand' }))
    fireEvent.click(screen.getByRole('button', { name: 'Test' }))
    expect(window.location.search).toBe('')   // the choices ride the history entry; Share writes them out
    first.unmount()
    draw(topic(body))
    expect(screen.getByRole('button', { name: 'Hand' }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByRole('button', { name: 'Test' }).getAttribute('aria-pressed')).toBe('true')
    // The start writes nothing: back on the first picture and Explore, a fresh visit.
    fireEvent.click(screen.getByRole('button', { name: 'Face' }))
    fireEvent.click(screen.getByRole('button', { name: 'Explore' }))
    expect(window.history.state?.view?.board).toBeUndefined()
    expect(window.history.state?.view?.step).toBeUndefined()
  })

  it('a link naming a board the topic lacks opens on the first', () => {
    window.history.replaceState({ view: { words: 'picture', board: 'nowhere', step: 'test' } }, '', '/colloq/fusha/unit-23/lesson-01/words')
    draw(topic(body))
    expect(screen.getByRole('button', { name: 'Face' }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByRole('button', { name: 'Test' }).getAttribute('aria-pressed')).toBe('true')
  })
})
