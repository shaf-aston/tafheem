import 'fake-indexeddb/auto'
import { describe, expect, it } from 'vitest'

import { addBook, keepPage, listBooks, removeBook } from './library'

const pdf = (name, bytes = 'x') => new File([bytes], name, { type: 'application/pdf' })

describe('reader library', () => {
  it('keeps a book and the page it was left on, and the same file twice is one book', async () => {
    const book = await addBook(pdf('a.pdf'))
    await keepPage(book.id, 42)
    const again = await addBook(pdf('a.pdf'))
    expect(again.page).toBe(42)
    const books = await listBooks()
    expect(books.filter((b) => b.name === 'a.pdf')).toHaveLength(1)
    expect(await books[0].file.text()).toBe('x')
  })

  it('tells apart two files with one name', async () => {
    await addBook(pdf('b.pdf', 'one'))
    await addBook(pdf('b.pdf', 'three'))
    const books = await listBooks()
    expect(books.filter((b) => b.name === 'b.pdf')).toHaveLength(2)
  })

  it('forgets a removed book', async () => {
    const book = await addBook(pdf('c.pdf'))
    await removeBook(book.id)
    expect((await listBooks()).some((b) => b.id === book.id)).toBe(false)
  })
})
