// @vitest-environment happy-dom
// Grow's Basics world on the real word file: a tap from Home goes straight into the first lesson, which says what ال is,
// teaches "the book", then asks it both ways; every answer is filed under module 'basics'. A page load on the same address
// lands on Grow's home with the lesson offered instead.
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'

import { renderScreen } from './render'
import GrowPanel from '../components/GrowPanel'
import { definite } from '../lib/alifLam'
import { pathItems } from '../lib/basicsSkills'
import data from '../../public/grow/basics.json'
import verbs from '../../public/grow/basics-verbs.json'

const items = pathItems(data.words, { verbs: verbs.verbs, path: data.path })

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
    expect(screen.getAllByRole('radio').map((radio) => radio.textContent).sort()).toEqual(['a book', 'the book'])
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
    fireEvent.click(screen.getAllByRole('radio')[0])
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
})
