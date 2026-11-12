import { describe, expect, it } from 'vitest'

import { pagesOf, printedPageOf } from './memorise'

// Al-Ikhlas, as the surah endpoint hands it over.
const IKHLAS = [
  { id: 1, arabic: 'قُلْ هُوَ ٱللَّهُ أَحَدٌ' },
  { id: 2, arabic: 'ٱللَّهُ ٱلصَّمَدُ' },
  { id: 3, arabic: 'لَمْ يَلِدْ وَلَمْ يُولَدْ' },
  { id: 4, arabic: 'وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌۢ' },
]

describe('cutting a book into pages', () => {
  it('fills a page up to about the asked-for size and starts the next one', () => {
    const lines = Array.from({ length: 10 }, (_, i) => ({ id: i, arabic: 'ا ب ج د ه' }))
    const pages = pagesOf(lines, 12)
    // 5 words a line: two lines fit in 12, a third would make 15.
    expect(pages.map((p) => p.length)).toEqual([2, 2, 2, 2, 2])
  })

  it('never cuts a line in half, however long it is', () => {
    const long = { id: 1, arabic: Array(40).fill('كلمة').join(' ') }
    const pages = pagesOf([long, { id: 2, arabic: 'ا ب' }], 10)
    expect(pages[0]).toEqual([long])
    expect(pages[1]).toHaveLength(1)
  })

  it('loses no line and keeps them in order', () => {
    const pages = pagesOf(IKHLAS, 6)
    expect(pages.flat().map((l) => l.id)).toEqual([1, 2, 3, 4])
  })

  it('gives nothing back for nothing', () => {
    expect(pagesOf([])).toEqual([])
  })

  it('groups by the printed page when the lines know one, ignoring word count', () => {
    // Three short lines on one printed page and one long line on the next. By
    // word count these would break in the middle of page 30; by the printing
    // they do not, which is the whole point of having the layout.
    const lines = [
      { id: 1, arabic: 'ا ب', page: 30 },
      { id: 2, arabic: 'ج د', page: 30 },
      { id: 3, arabic: 'ه و ز ح ط ي ك ل', page: 30 },
      { id: 4, arabic: 'م ن', page: 31 },
    ]
    const pages = pagesOf(lines, 4)
    expect(pages.map((page) => page.map((line) => line.id))).toEqual([[1, 2, 3], [4]])
    expect(printedPageOf(pages[0])).toBe(30)
    expect(printedPageOf(pages[1])).toBe(31)
  })

  it('keeps a line with no page number on the page already open', () => {
    // A hole in the layout must not start a page of its own, or one unlisted
    // ayah would silently split a printed page in two.
    const lines = [
      { id: 1, arabic: 'ا', page: 5 },
      { id: 2, arabic: 'ب' },
      { id: 3, arabic: 'ج', page: 6 },
    ]
    expect(pagesOf(lines).map((page) => page.map((line) => line.id))).toEqual([[1, 2], [3]])
  })

  it('says a word-counted page has no printed number rather than inventing one', () => {
    expect(printedPageOf(pagesOf(IKHLAS, 6)[0])).toBe(null)
  })
})

describe('where a page ends', () => {
  const line = (id, n) => ({ id, arabic: Array(n).fill('ك').join(' ') })

  it('takes a line that lands exactly on the page size, and breaks at the next', () => {
    // 5 + 5 is exactly 10: that page is full, not over.
    const pages = pagesOf([line(1, 5), line(2, 5), line(3, 5)], 10)
    expect(pages.map((p) => p.map((l) => l.id))).toEqual([[1, 2], [3]])
  })

  it('breaks one word past the page size once the page is half full', () => {
    // 5 is half of 10, so a sixth word over is where the page closes.
    expect(pagesOf([line(1, 5), line(2, 6)], 10).map((p) => p.length)).toEqual([1, 1])
  })

  it('keeps pulling lines in while the page is under half full, even past the size', () => {
    expect(pagesOf([line(1, 4), line(2, 7)], 10).map((p) => p.length)).toEqual([2])
  })
})
