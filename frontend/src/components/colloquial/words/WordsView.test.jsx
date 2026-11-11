// @vitest-environment happy-dom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import spine from '../../../../../backend/data/colloquial/spine.json'
import WordsView from './WordsView'
import { speak } from '../../../lib/speech/speak'

vi.mock('../../../lib/speech/speak', () => ({ speak: vi.fn(), prepare: vi.fn(), stop: vi.fn() }))
vi.mock('../../../lib/learner/record', () => ({ useRecord: () => ({ file: vi.fn() }), summaryQuery: () => ({ queryKey: ['summary'], queryFn: async () => [] }) }))

const word = (id) => ({ id, english: id, arabic: `ك${id}`, transliteration: id, category: 'things' })
const topic = (ids) => ({ lesson: 'lesson-01', title: 'A topic', written: true, phrases: [], vocabulary: ids.map(word) })
const unit = (lesson) => ({ unit: 'unit-23', dialect_key: 'fusha', title: 'U', lessons: [lesson] })
const body = spine.units.flatMap((u) => u.lessons).find((l) => l.title === 'The Body, Head to Toe').words

const draw = (lesson) => render(<QueryClientProvider client={new QueryClient()}><WordsView unit={unit(lesson)} at={0} /></QueryClientProvider>)
const on = () => screen.getByRole('group', { name: 'How to learn the words' }).querySelector('[aria-pressed=true]').textContent

beforeEach(() => { globalThis.scrollTo = vi.fn(); window.history.replaceState({}, '', '/colloq/fusha/unit-23/lesson-01/words') })
afterEach(cleanup)

describe('WordsView: Browse, with the drawing where the words have one', () => {
  it('a topic with a drawing opens on Browse with the drawing in it, and has no tab of its own for it', () => {
    draw(topic(body))
    expect(on()).toBe('Browse')
    expect(screen.getByRole('button', { name: 'Face' })).toBeTruthy()   // the drawing's boards
    expect(screen.getByRole('button', { name: 'Explore' })).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Picture' })).toBeNull()
    const tabs = [...screen.getByRole('group', { name: 'How to learn the words' }).querySelectorAll('button')].map((b) => b.textContent)
    expect(tabs).toEqual(['Browse', 'Cards', 'Match', 'Quiz', 'Review'])
  })

  it('the drawing sits beside the words in a wide layout and the words run in a narrow column', () => {
    const { container } = draw(topic(body))
    const split = container.querySelector('.lg\\:grid')
    expect(split).not.toBeNull()
    expect(split.querySelector('.lg\\:sticky')).not.toBeNull()   // the drawing is held in view
    // The picker and the question are held beside it (not above it), so none of the exercise scrolls away.
    const held = [...split.querySelectorAll('.lg\\:sticky')]
    const beside = held.find((e) => e.querySelector('[aria-live=polite]'))
    expect(beside.className).toContain('lg:col-start-2')
    expect(beside.contains(screen.getByRole('button', { name: 'Explore' }))).toBe(true)
    expect(held.find((e) => e.querySelector('svg')).className).toContain('lg:col-start-1')
    // The words under it use the narrow mosaic (3 across at most), not the 6-across wide one.
    expect(container.querySelector('ul.grid.sm\\:grid-cols-3')).not.toBeNull()
    expect(container.querySelector('ul.grid.lg\\:grid-cols-6')).toBeNull()
  })

  it('a topic with no drawing is the plain Browse, the wide mosaic and nothing beside it', () => {
    const { container } = draw(topic(['apple', 'bread', 'rice']))
    expect(on()).toBe('Browse')
    expect(screen.queryByRole('button', { name: 'Explore' })).toBeNull()
    expect(container.querySelector('.lg\\:sticky')).toBeNull()
  })

  it('an old ?words=picture link opens Browse', () => {
    window.history.replaceState({ view: { words: 'picture' } }, '', '/colloq/fusha/unit-23/lesson-01/words')
    draw(topic(body))
    expect(on()).toBe('Browse')
    expect(screen.getByRole('button', { name: 'Face' })).toBeTruthy()
  })

  it('tapping a dot says its word through the speaker button: busy while the voice is made, and failed if it cannot', async () => {
    let fail
    speak.mockReturnValueOnce(new Promise((_, reject) => { fail = reject }))
    const { container } = draw(topic(body))
    fireEvent.click(container.querySelector('circle[data-key]'))
    const button = await screen.findByRole('button', { name: 'Say it aloud' })
    expect(speak).toHaveBeenCalledTimes(1)
    expect(button.getAttribute('aria-busy')).toBe('true')   // not silent: the screen says it is working
    fail(new Error('No voice could say this'))
    expect((await screen.findByRole('button', { name: 'No voice could say this' }))).toBeTruthy()   // and says when it cannot
  })

  it('a mode picked is kept across a reload', () => {
    const first = draw(topic(body))
    fireEvent.click(screen.getByRole('button', { name: 'Cards' }))
    first.unmount()
    draw(topic(body))
    expect(on()).toBe('Cards')
  })

  it('the board and the Explore/Test step are kept across a reload and in a link', () => {
    const first = draw(topic(body))
    fireEvent.click(screen.getByRole('button', { name: 'Hand' }))
    fireEvent.click(screen.getByRole('button', { name: 'Test' }))
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
    window.history.replaceState({ view: { board: 'nowhere', step: 'test' } }, '', '/colloq/fusha/unit-23/lesson-01/words')
    draw(topic(body))
    expect(screen.getByRole('button', { name: 'Face' }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByRole('button', { name: 'Test' }).getAttribute('aria-pressed')).toBe('true')
  })
})
