import { describe, expect, it } from 'vitest'

import { bookOf, listOf, narratorOf, narratorPlaceOf, parsePlace, placeOf, shortOf } from './hadithPlace'

const collections = [{ id: 'bukhari', name: 'Sahih al-Bukhari' }]

describe('parsePlace', () => {
  it('reads a collection, a book, and one hadith with and without a part letter', () => {
    expect(parsePlace('bukhari', collections)).toEqual({ collection: 'bukhari', book: null, number: null, part: '' })
    expect(parsePlace('bukhari/1', collections)).toEqual({ collection: 'bukhari', book: 1, number: null, part: '' })
    expect(parsePlace('bukhari/1/2', collections)).toEqual({ collection: 'bukhari', book: 1, number: 2, part: '' })
    expect(parsePlace('bukhari/1/2a', collections)).toEqual({ collection: 'bukhari', book: 1, number: 2, part: 'a' })
  })

  it.each([
    '', null, 'muslim', 'muslim/1', 'bukhari/one', 'bukhari/1/two', 'bukhari/1/2/extra', '/1',
  ])('refuses %j', (q) => {
    expect(parsePlace(q, collections)).toBeNull()
  })

  it('writes back what it reads, at every depth', () => {
    expect(parsePlace(placeOf('bukhari'), collections)).toEqual({ collection: 'bukhari', book: null, number: null, part: '' })
    expect(parsePlace(placeOf('bukhari', 1), collections)).toEqual({ collection: 'bukhari', book: 1, number: null, part: '' })
    expect(parsePlace(placeOf('bukhari', 1, 2, 'a'), collections)).toEqual({ collection: 'bukhari', book: 1, number: 2, part: 'a' })
  })
})

describe('shortOf', () => {
  const books = [{ number: 1 }, { number: 54 }]
  it('reads a number with no book of that number, or with a letter, as a hadith', () => {
    expect(shortOf('muslim/2927', books)).toBe('muslim')
    expect(shortOf('muslim/2927a', books)).toBe('muslim')
    expect(shortOf('muslim/54a', books)).toBe('muslim')
  })
  it.each([
    ['muslim/54', books], ['muslim/2927', undefined], ['muslim/54/2927a', books], ['muslim', books], ['muslim/x', books],
  ])('leaves %j to parsePlace', (q, b) => {
    expect(shortOf(q, b)).toBeNull()
  })
})

describe('narrator places', () => {
  it('writes and reads a narrator page, and no other place is one', () => {
    expect(narratorOf(narratorPlaceOf(6659))).toBe('6659')
    expect(['muslim/24', 'narrator/x', 'narrator/1/2', null].map(narratorOf)).toEqual([null, null, null, null])
  })

  it('is not mistaken for a book to prefetch', () => {
    expect(bookOf('narrator/6659')).toBeNull()
    expect(bookOf('muslim/24')).toEqual(['muslim', 24])
  })
})

describe('list places', () => {
  it('knows the narrators and scholars lists, and no other place is one', () => {
    expect(['narrators', 'scholars'].map(listOf)).toEqual(['narrators', 'scholars'])
    expect(['bukhari', 'narrator/1', '', null].map(listOf)).toEqual([null, null, null, null])
  })

  it('is not mistaken for a book to prefetch', () => {
    expect(bookOf('scholars/2')).toBeNull()
  })
})
