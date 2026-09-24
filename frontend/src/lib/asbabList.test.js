import { describe, expect, it } from 'vitest'
import settings from '../timelines.json'
import { bySurah, matching, needsSearch, quotedWords, reportsIn } from './asbabList'

const report = (ref, name, opening = '') => {
  const [surah, ayah] = ref.split(':').map(Number)
  return { ref, surah, ayah, surah_name: name, opening, how: 'period' }
}
const REPORTS = [
  report('8:9', 'Al-Anfal', 'when you were asking help of your Lord'),
  report('2:30', 'Al-Baqarah', 'about the angels'),
  report('2:6', 'Al-Baqarah', 'about the disbelievers of Makkah'),
]

describe('bySurah', () => {
  it('groups by surah in mushaf order, each group in ayah order', () => {
    expect(bySurah(REPORTS).map((g) => [g.surah, g.reports.map((r) => r.ayah)]))
      .toEqual([[2, [6, 30]], [8, [9]]])
  })

  it('is empty for no reports at all', () => {
    expect(bySurah(undefined)).toEqual([])
  })
})

describe('matching', () => {
  it.each([
    ['8:9', ['8:9']],
    ['2', ['2:30', '2:6']],
    ['baqarah', ['2:30', '2:6']],
    ['angels', ['2:30']],
    ['nothing here', []],
  ])('%j keeps %j', (query, refs) => {
    expect(matching(REPORTS, query).map((r) => r.ref)).toEqual(refs)
  })

  it('reads an address as an address, never as a prefix', () => {
    // 2:3 is the third ayah. Answering with the thirtieth is the kind of wrong
    // answer nobody notices, which is worse than no answer.
    expect(matching(REPORTS, '2:3')).toEqual([])
    expect(matching(REPORTS, '2:30').map((r) => r.ref)).toEqual(['2:30'])
    expect(matching(REPORTS, '8').map((r) => r.ref)).toEqual(['8:9'])
  })

  it('keeps every report when nothing is typed', () => {
    expect(matching(REPORTS, '  ')).toHaveLength(3)
  })
})

describe('needsSearch', () => {
  it('follows the knob rather than a number written here', () => {
    const from = settings.asbab['search-from']
    expect(needsSearch(from)).toBe(true)
    expect(needsSearch(from - 1)).toBe(false)
  })
})

describe('reportsIn', () => {
  it('splits a passage back into the reports the book gives on that ayah', () => {
    expect(reportsIn('[1 / 2] first report\n\n[2 / 2] second report'))
      .toEqual(['first report', 'second report'])
  })

  it('leaves a single report whole, markers or not', () => {
    expect(reportsIn('one report only')).toEqual(['one report only'])
  })

  it('has nothing to show for nothing', () => {
    expect(reportsIn('')).toEqual([])
    expect(reportsIn(undefined)).toEqual([])
  })
})

describe('quotedWords', () => {
  it('keeps only the ayah words, not who narrated it', () => {
    expect(quotedWords(`Concerning Allah's words "And to Allah belongs the east": Muslim reported`)).toBe('And to Allah belongs the east')
  })

  it('reads single quotes too, keeping an apostrophe inside them', () => {
    expect(quotedWords(`Concerning Allah's words 'And if you punish, it's equal': al-Hakim reported`)).toBe(`And if you punish, it's equal`)
  })

  it('ends at the closing quote whatever follows it', () => {
    expect(quotedWords(`Concerning Allah's words 'And if you punish...' [to the end]:\nAl-Hakim`)).toBe('And if you punish...')
    expect(quotedWords(`Concerning Allah's words "O mankind...", the verse:\nIbn Abi Hatim`)).toBe('O mankind...')
  })

  it('keeps an opening in any other shape whole, and survives nothing', () => {
    expect(quotedWords('Ibn Abbas said: it came down at Badr')).toBe('Ibn Abbas said: it came down at Badr')
    expect(quotedWords(undefined)).toBe('')
  })
})
