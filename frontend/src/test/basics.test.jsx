// @vitest-environment happy-dom
// Grow's Basics world on the real word file: a tap from Home goes straight into the first lesson, which says what ال is,
// teaches "the book", then asks it both ways; every answer is filed under module 'basics'. A page load on the same address
// lands on Grow's home with the lesson offered instead.
import { describe, expect, it } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'

import { renderScreen } from './render'
import GrowPanel from '../components/GrowPanel'
import { definite } from '../lib/alifLam'

const click = (name) => fireEvent.click(screen.getByRole('button', { name }))

function routes(filed = []) {
  return {
    'GET /progress/summary': { items: [] },
    'POST /progress/attempts': (config) => { filed.push(JSON.parse(config.data)); return { earned: 1 } },
  }
}

describe('basics', () => {
  it('a tap from another tab opens the first lesson on what ال is, then asks "the book" both ways', async () => {
    const filed = []
    renderScreen(<GrowPanel incoming="basics/lesson" arrival={1} onVisit={() => {}} />, { routes: routes(filed) })

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

  it('a page load on the lesson address lands on Grow home, with the lesson offered', async () => {
    renderScreen(<GrowPanel incoming="basics/lesson" arrival={0} onVisit={() => {}} />, { routes: routes() })
    expect(await screen.findByRole('heading', { name: 'Basics' })).toBeTruthy()
    expect(screen.queryByText('means “the”')).toBeNull()
  })
})
