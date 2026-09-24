import { describe, expect, it } from 'vitest'

import { GROUPS, classify, ghostFor, grouped } from './commandRoutes'

const TABS = [
  { id: 'nahw', label: 'Nahw', short: 'Nahw', arabic: 'نحو' },
  { id: 'sarf', label: 'Sarf', short: 'Sarf', arabic: 'صرف' },
  { id: 'quran', label: 'Quran', short: 'Quran', arabic: 'القرآن' },
  { id: 'daleel', label: 'Daleel', short: 'Daleel', arabic: 'دليل' },
  { id: 'mem', label: 'Memorise', short: 'Mem', arabic: 'حفظ' },
  { id: 'dict', label: 'Dictionary', short: 'Dict', arabic: 'قاموس' },
  { id: 'quiz', label: 'Quiz', short: 'Quiz', arabic: 'اختبار' },
]

describe('classify', () => {
  it('says nothing about an empty line', () => {
    expect(classify('', TABS)).toEqual([])
    expect(classify('   ', TABS)).toEqual([])
  })

  it('reads an ayah address and sends it to the Quran tab', () => {
    const [row] = classify('2:255', TABS)
    expect(row).toMatchObject({ group: GROUPS.ayah, tabId: 'quran', value: '2:255' })
  })

  it('accepts the Arabic comma a keyboard left in Arabic types', () => {
    expect(classify('2٬255', TABS)[0].value).toBe('2:255')
  })

  it('drops leading zeros so 002:007 and 2:7 are one address', () => {
    expect(classify('002:007', TABS)[0].value).toBe('2:7')
  })

  it('refuses a surah number that does not exist', () => {
    const rows = classify('300:1', TABS)
    expect(rows.every((row) => row.group !== GROUPS.ayah)).toBe(true)
  })

  it('looks a root up in three places when @ is used', () => {
    const rows = classify('@قول', TABS)
    expect(rows.map((row) => row.tabId)).toEqual(['dict', 'sarf', 'quran'])
    expect(rows.every((row) => row.value === 'قول')).toBe(true)
  })

  it('gives nothing for a bare @ rather than searching for an empty root', () => {
    expect(classify('@', TABS)).toEqual([])
  })

  it('only names tabs after a slash, even when the name is wrong', () => {
    expect(classify('/dict', TABS).map((row) => row.tabId)).toEqual(['dict'])
    expect(classify('/zzz', TABS)).toEqual([])
  })

  it('matches a tab by its Arabic name too', () => {
    expect(classify('/قاموس', TABS).map((row) => row.tabId)).toEqual(['dict'])
  })

  it('offers a lookup and an analysis for one Arabic word', () => {
    const rows = classify('كتاب', TABS)
    expect(rows.map((row) => row.tabId)).toEqual(['dict', 'sarf', 'nahw'])
  })

  it('sends a whole Arabic sentence straight to the analyser', () => {
    const rows = classify('ذهب الولد إلى المدرسة', TABS)
    expect(rows).toHaveLength(1)
    expect(rows[0]).toMatchObject({ group: GROUPS.ask, tabId: 'nahw' })
  })

  it('never ends on nothing: plain English still lands somewhere', () => {
    const rows = classify('what is a mubtada', TABS)
    expect(rows.length).toBeGreaterThan(0)
    expect(rows.at(-1).tabId).toBe('nahw')
  })

  it('lists a matching tab before the fallback', () => {
    const rows = classify('qui', TABS)
    expect(rows[0]).toMatchObject({ group: GROUPS.go, tabId: 'quiz' })
    expect(rows.at(-1).group).toBe(GROUPS.ask)
  })
})

describe('ghostFor', () => {
  it('completes a tab name being typed', () => {
    expect(ghostFor('dic', TABS)).toBe('tionary')
    expect(ghostFor('/mem', TABS)).toBe('orise')
  })

  it('stops once the name is whole', () => {
    expect(ghostFor('Quiz', TABS)).toBe('')
  })

  it('never guesses past a root or an address', () => {
    expect(ghostFor('@قو', TABS)).toBe('')
    expect(ghostFor('2:25', TABS)).toBe('')
    expect(ghostFor('كتا', TABS)).toBe('')
  })
})

describe('grouped', () => {
  it('keeps the display order and drops empty groups', () => {
    expect(grouped(classify('@قول', TABS)).map((block) => block.group)).toEqual([GROUPS.dict])
    expect(grouped(classify('qui', TABS)).map((block) => block.group)).toEqual([GROUPS.go, GROUPS.ask])
  })
})

describe('a surah named with an ayah', () => {
  it('opens the ayah for "Nisa 45"', () => {
    const [row] = classify('Nisa 45', TABS)
    expect(row).toMatchObject({ group: GROUPS.ayah, tabId: 'quran', value: '4:45', label: 'An-Nisa 45' })
  })

  it('offers nothing when the ayah is past the end of that surah', () => {
    expect(classify('nisa 177', TABS).some((r) => r.group === GROUPS.ayah)).toBe(false)
  })

  it('leaves a bare name and ordinary words to the tabs', () => {
    expect(classify('nisa', TABS).some((r) => r.group === GROUPS.ayah)).toBe(false)
    expect(classify('quiz 3', TABS).some((r) => r.group === GROUPS.ayah)).toBe(false)
  })

  it('does not steal a root lookup or a slash command', () => {
    expect(classify('@نور 3', TABS).every((r) => r.group !== GROUPS.ayah)).toBe(true)
    expect(classify('/nisa 4', TABS).every((r) => r.group !== GROUPS.ayah)).toBe(true)
  })
})
