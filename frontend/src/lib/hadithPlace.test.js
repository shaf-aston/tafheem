import { describe, expect, it } from 'vitest'

import { parsePlace, placeOf } from './hadithPlace'

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
