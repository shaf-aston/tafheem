// @vitest-environment happy-dom
// Grow's Basics world on the real word file: a tap from Home goes straight into the first lesson, which says what ال is,
// teaches "the book", then asks it both ways; every answer is filed under module 'basics'. A page load on the same address
// lands on Grow's home with the lesson offered instead.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'

import { renderScreen } from './render'
import GrowPanel from '../components/grow/GrowPanel'
import { definite } from '../lib/grow/alifLam'
import { pathItems } from '../lib/grow/basicsSkills'
import { LEVEL_KEY } from '../lib/learner/learnerLevel'
import { writeRaw } from '../lib/store/stored'
import data from '../../public/grow/basics.json'
import verbs from '../../public/grow/basics-verbs.json'

const items = pathItems(data.words, { verbs: verbs.verbs, people: data.people, path: data.path })

const click = (name) => fireEvent.click(screen.getByRole('button', { name }))

function routes(filed = []) {
  return {
    'GET /progress/summary': { items: [] },
    'POST /progress/attempts': (config) => { filed.push(JSON.parse(config.data)); return { earned: 1 } },
  }
}

// The record every guest shares: `rows` for the Basics, nothing for any other world.
const shared = (rows) => ({
  'GET /progress/summary': (config) => ({ items: config.params.module === 'basics' ? rows : [] }),
  'POST /progress/attempts': { earned: 1 },
})
const seen = (id, due = false) => ({ item: id, due, dueAt: '2026-10-23T00:00:00Z', known: false })
const home = () => <GrowPanel incoming={null} arrival={null} onVisit={() => {}} />
const hero = () => screen.findByRole('heading', { level: 3, name: /Your first steps|Keep your garden growing/ })

describe('basics', () => {
  beforeEach(() => localStorage.clear())

  it('a world opens at its top, not where Grow\'s page was scrolled to', async () => {
    renderScreen(home(), { routes: routes() })
    await hero()
    const scrolled = vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
    fireEvent.click(document.querySelector('.grow-world-tile'))
    await waitFor(() => expect(scrolled).toHaveBeenCalledWith(expect.objectContaining({ top: 0 })))
    scrolled.mockRestore()
  })

  it('back to Grow\'s page lands where the reader left it', async () => {
    renderScreen(home(), { routes: routes() })
    await hero()
    const scrolled = vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
    window.scrollY = 500
    fireEvent.scroll(window)
    fireEvent.click(document.querySelector('.grow-world-tile'))
    await waitFor(() => expect(scrolled).toHaveBeenCalledWith(expect.objectContaining({ top: 0 })))
    fireEvent.click(document.querySelector('.grow-back'))
    await waitFor(() => expect(scrolled).toHaveBeenCalledWith(expect.objectContaining({ top: 500 })))
    scrolled.mockRestore()
    window.scrollY = 0
  })

  it('a tap from another tab opens the first lesson on what ال is, then asks "the book" both ways', async () => {
    const filed = []
    renderScreen(<GrowPanel incoming="basics/lesson" arrival={1} handed onVisit={() => {}} />, { routes: routes(filed) })

    expect(await screen.findByText('means “the”')).toBeTruthy()
    expect(screen.getByText('the book')).toBeTruthy()
    click('Continue')
    // The first word, with ال and without it.
    expect(screen.getByText('a book')).toBeTruthy()
    click('Continue')

    expect(screen.getByText('Which one is “the book”?')).toBeTruthy()
    expect(screen.getAllByRole('radio')).toHaveLength(3)
    fireEvent.click(screen.getByRole('radio', { name: definite('كِتَاب') }))
    click('Check')
    expect(screen.getByRole('status').textContent).toMatch(/joined to the front of the word/)
    await waitFor(() => expect(filed.at(-1)).toMatchObject({
      module: 'basics', item: 'book', correct: true, context: { world: 'basics', direction: 'to-arabic' },
    }))

    click('Continue')
    expect(screen.getByText('What does it mean?')).toBeTruthy()
    expect(screen.getAllByRole('radio').map((radio) => radio.lastChild.textContent).sort()).toEqual(['a book', 'the book'])
  })

  it.each([['a page load', 0], ['the Grow tab reopened on its saved place', 2]])('%s on a lesson address lands on Grow home, with the lesson offered', async (_, arrival) => {
    renderScreen(<GrowPanel incoming="basics/lesson" arrival={arrival} onVisit={() => {}} />, { routes: routes() })
    expect(await screen.findByRole('heading', { name: 'Basics' })).toBeTruthy()
    expect(screen.queryByText('means “the”')).toBeNull()
  })

  it("another guest's answers on the shared record neither skip a newcomer's opening card nor change their Today", async () => {
    const { unmount } = renderScreen(home(), { routes: shared([seen('book'), seen('sun', true)]) })
    // Not begun on this device: Today leads with the words, and offers the Basics as a start.
    expect((await hero()).textContent).toBe('Keep your garden growing')
    expect(screen.queryByRole('button', { name: /Basics · Your first steps/ })).toBeNull()
    fireEvent.click(await screen.findByRole('button', { name: /New to Arabic\?/ }))
    expect(await screen.findByText('means “the”')).toBeTruthy()
    unmount()

    // Begun here now: the Basics lead Today, the words become a step, and the start offer is gone.
    renderScreen(home(), { routes: shared([seen('book'), seen('sun', true)]) })
    expect((await hero()).textContent).toBe('Your first steps')
    expect(await screen.findByRole('button', { name: /Words · Today’s words/ })).toBeTruthy()
    expect(screen.queryByRole('button', { name: /New to Arabic\?/ })).toBeNull()
  })

  it('after the first ten words, teaches “my” with its rule, then asks it on a word of its own', async () => {
    localStorage.setItem('basics-begun', 'on')
    const filed = []
    const rows = items.slice(0, 10).map((item) => seen(item.id))
    renderScreen(<GrowPanel incoming="basics/lesson" arrival={1} handed onVisit={() => {}} />, {
      routes: { ...shared(rows), 'POST /progress/attempts': (config) => { filed.push(JSON.parse(config.data)); return { earned: 1 } } },
    })

    expect(await screen.findByText('my book')).toBeTruthy()
    expect(screen.getByText('a book')).toBeTruthy()
    expect(screen.getByText(/on the end means “my”/)).toBeTruthy()
    click('Continue')

    expect(screen.getByText(/^Which one is “my .+”\?$/)).toBeTruthy()
    expect(screen.getAllByRole('radio')).toHaveLength(3)
    // The options are shuffled; the right one has neither ال nor a final ة before the ending.
    fireEvent.click(screen.getAllByRole('radio').find((option) => !/^ال|ة/.test(option.lastChild.textContent.trim())))
    click('Check')
    expect(screen.getByRole('status').textContent).toMatch(/on the end means “my”/)
    await waitFor(() => expect(filed.at(-1)).toMatchObject({
      module: 'basics', item: 'mine:my', context: { world: 'basics', skill: 'mine', direction: 'to-arabic' },
    }))
  })

  describe('with the verbs file missing (offline, or before it was saved)', () => {
    const served = globalThis.fetch
    beforeEach(() => {
      globalThis.fetch = (input) => (String(input).endsWith('/basics-verbs.json') ? Promise.resolve(new Response('', { status: 404 })) : served(input))
    })
    afterEach(() => { globalThis.fetch = served })

    it('still opens the first lesson on the words', async () => {
      renderScreen(<GrowPanel incoming="basics/lesson" arrival={1} handed onVisit={() => {}} />, { routes: routes() })
      expect(await screen.findByText('means “the”')).toBeTruthy()
      click('Continue')
      expect(screen.getByText('a book')).toBeTruthy()
    })
  })

  it('reads “new steps” on Today, since a step can be a word or an addition', async () => {
    localStorage.setItem('basics-begun', 'on')
    renderScreen(home(), { routes: shared([seen('book')]) })
    expect(await screen.findByText(/\d new steps · \d to review/)).toBeTruthy()
  })

  it('stops leading Today once every step has been met and none is due', async () => {
    localStorage.setItem('basics-begun', 'on')
    renderScreen(home(), { routes: shared(items.map((item) => seen(item.id))) })
    // While the record loads the Basics hold the place, so nothing flips for a learner still on them.
    await waitFor(async () => expect((await hero()).textContent).toBe('Keep your garden growing'))
    expect(screen.queryByRole('button', { name: /Basics · / })).toBeNull()
  })

  describe('Today by the learner\'s level', () => {
    it('leads a beginner with the Basics before they have begun them, without offering them twice', async () => {
      writeRaw(LEVEL_KEY, 'beginner')
      renderScreen(home(), { routes: shared([]) })
      await waitFor(async () => expect((await hero()).textContent).toBe('Your first steps'))
      expect(screen.queryByRole('button', { name: /New to Arabic\?/ })).toBeNull()
    })

    it('leads an intermediate learner with the words, and does not offer the Basics', async () => {
      writeRaw(LEVEL_KEY, 'intermediate')
      renderScreen(home(), { routes: shared([]) })
      await waitFor(async () => expect((await hero()).textContent).toBe('Keep your garden growing'))
      expect(screen.queryByRole('button', { name: /New to Arabic\?/ })).toBeNull()
    })

    it('leads an advanced learner with Nahw, the first book of grammar', async () => {
      writeRaw(LEVEL_KEY, 'advanced')
      renderScreen(home(), { routes: shared([]) })
      expect(await screen.findByText('Continue · Nahw', {}, { timeout: 3000 })).toBeTruthy()
    })
  })
})
