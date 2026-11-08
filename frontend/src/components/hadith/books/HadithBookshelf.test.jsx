// @vitest-environment happy-dom
// The six stay on the tab's shelf; the further books (Mishkat and the rest) stand in the bookshelf at its end.
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, screen, within } from '@testing-library/react'

import { renderScreen } from '../../../test/render'
import HadithCollectionPicker from './HadithCollectionPicker'
import HadithBookshelf from './HadithBookshelf'
import { shelvesOf } from '../useHadithCollections'

const COLLECTIONS = [
  { id: 'bukhari', name: 'Sahih al-Bukhari', short: 'Bukhari', sahih: true },
  { id: 'muslim', name: 'Sahih Muslim', short: 'Muslim', sahih: true },
  { id: 'mishkat', name: 'Mishkat al-Masabih', short: 'Mishkat', arabic: 'مشكاة المصابيح', shelf: 'Gathered by topic',
    count: 4428 },
  { id: 'nawawi', name: 'Forty Hadith of an-Nawawi', short: 'Nawawi', shelf: 'Forty hadith', count: 42 },
]
const ROUTES = { 'GET /hadith/collections': COLLECTIONS }

afterEach(cleanup)

describe('the bookshelf', () => {
  it('keeps the further books off the shelf, behind the bookshelf at its end', async () => {
    const onBookshelf = vi.fn()
    renderScreen(<HadithCollectionPicker value="bukhari" onChange={() => {}} onBookshelf={onBookshelf} />, { routes: ROUTES })
    const shelf = await screen.findByRole('group', { name: 'Collection' })
    expect(within(shelf).getAllByRole('button').map((b) => b.textContent)).toEqual(['Bukhari', 'Muslim', 'More books'])
    fireEvent.click(within(shelf).getByRole('button', { name: 'More books' }))
    expect(onBookshelf).toHaveBeenCalled()
  })

  it('stands an open further book on the shelf beside the bookshelf, so the shelf says which book this is', async () => {
    renderScreen(<HadithCollectionPicker value="mishkat" onChange={() => {}} onBookshelf={() => {}} />, { routes: ROUTES })
    const open = await screen.findByRole('button', { name: 'Mishkat' })
    expect(open.getAttribute('aria-pressed')).toBe('true')
  })

  it('lays the books out shelf by shelf, each with its cover, name and count, and opens the one picked', async () => {
    const onPick = vi.fn()
    renderScreen(<HadithBookshelf onPick={onPick} />, { routes: ROUTES })
    const topic = await screen.findByRole('region', { name: 'Gathered by topic' })
    expect(within(topic).getByText('مشكاة المصابيح')).toBeTruthy()
    expect(within(topic).getByText('4,428 hadiths')).toBeTruthy()
    expect(screen.getByRole('region', { name: 'Forty hadith' })).toBeTruthy()
    fireEvent.click(within(topic).getByRole('button', { name: /Mishkat al-Masabih/ }))
    expect(onPick).toHaveBeenCalledWith('mishkat')
  })

  it('groups by shelf in the order the books are listed', () => {
    expect(shelvesOf(COLLECTIONS).map(([shelf, books]) => [shelf, books.map((b) => b.id)]))
      .toEqual([['Gathered by topic', ['mishkat']], ['Forty hadith', ['nawawi']]])
  })
})
