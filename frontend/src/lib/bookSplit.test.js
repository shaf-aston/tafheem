import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

import { indexOf, indexPath, partOf, partPath, servedFile } from './bookSplit'
import { partOfLesson, partsDue, partsOf } from './bookLesson'

const book = JSON.parse(readFileSync(join(import.meta.dirname, '../../public/grow/quduri.json'), 'utf8'))
const row = (item, extra = {}) => ({ item, known: false, due: false, dueAt: '2026-01-01', ...extra })

describe('a book split for the page', () => {
  it('serves an index and a file per part beside the authored book', () => {
    expect(indexPath('/grow/quduri.json')).toBe('/grow/quduri/index.json')
    expect(partPath('/grow/quduri.json', 'tahara')).toBe('/grow/quduri/tahara.json')
  })

  it('keeps no cards in the index, only each lesson’s question ids, and is a small part of the book', () => {
    const index = indexOf(book)
    expect(index.parts.flatMap((part) => part.lessons).some((lesson) => lesson.cards)).toBe(false)
    const wudu = index.parts[0].lessons[0]
    expect(wudu.asks).toEqual(book.parts[0].lessons[0].cards.filter((card) => card.kind !== 'teach').map((card) => card.id))
    expect(JSON.stringify(index).length).toBeLessThan(JSON.stringify(book).length / 10)
  })

  it('reads every lesson’s status the same from the index as from the whole book', () => {
    const summary = [row('wudu/which-fard'), row('wudu/sort', { due: true }), row('nawaqid/blood-case')]
    const whole = partsOf(book, summary)
    const index = partsOf(indexOf(book), summary)
    const statuses = (state) => state.parts.flatMap((part) => part.lessons.map((lesson) => lesson.status))
    expect(statuses(index)).toEqual(statuses(whole))
    expect(index.next.id).toBe(whole.next.id)
    expect(index.due).toEqual(whole.due)
  })

  it('serves a part whole, and nothing for a part or file it does not have', () => {
    expect(servedFile(book, 'tahara.json')).toBe(partOf(book, 'tahara'))
    expect(servedFile(book, 'nowhere.json')).toBe(null)
  })

  it('tells which part a lesson, or a review of due items, needs', () => {
    const index = indexOf(book)
    expect(partOfLesson(index, 'wudu')).toBe('tahara')
    expect(partOfLesson(index, 'nowhere')).toBe(null)
    expect(partsDue(index, ['wudu/sort', 'salah-fard/which-fard', 'wudu/order']).sort()).toEqual(['salah', 'tahara'])
  })
})
