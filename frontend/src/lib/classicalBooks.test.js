import { describe, expect, it } from 'vitest'

import { classicalBooks, MAQAYEES } from './classicalBooks'

describe('classicalBooks', () => {
  it('is Ibn Faris alone before any other book has answered', () => {
    expect(classicalBooks().map((b) => b.id)).toEqual([MAQAYEES])
  })

  it('keeps the configured order and offers only books that sent an entry', () => {
    const entries = [{ book: 'lane', title: 'Lane' }, { book: 'lisan', title: 'لسان العرب' }]
    expect(classicalBooks(entries).map((b) => b.id)).toEqual([MAQAYEES, 'lisan', 'lane'])
  })

  it('puts a book the config does not know at the end, under its own title', () => {
    const books = classicalBooks([{ book: 'ain', title: 'كتاب العين' }])
    expect(books.at(-1)).toEqual({ id: 'ain', label: 'كتاب العين' })
  })
})
