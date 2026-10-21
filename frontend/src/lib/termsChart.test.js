import { describe, expect, it } from 'vitest'

import { layoutChart } from './pbsLayout'
import { branchChart, termAt, termsChart } from './termsChart'

const glossary = [
  { title: 'Accepted', name: 'المقبول', terms: [
    { arabic: 'الصحيح', en: 'Sahih', kids: [{ arabic: 'لذاته', en: 'in itself', kids: [] }, { arabic: 'لغيره', en: 'by support' }] },
    { arabic: 'الحسن', en: 'Hasan', kids: [] },
  ] },
  { title: 'Rejected', name: 'المردود', terms: [{ arabic: 'الضعيف', en: 'Weak' }] },
]

describe('termsChart', () => {
  it('roots the tree and makes a branch of each group', () => {
    const chart = termsChart(glossary)
    expect(chart.root).toEqual({ ar: 'مصطلح الحديث', en: 'Hadith terms' })
    expect(chart.branches.map((b) => [b.ar, b.en])).toEqual([['المقبول', 'Accepted'], ['المردود', 'Rejected']])
  })

  it('lists each group\'s terms as tappable pairs', () => {
    expect(termsChart(glossary).branches[0].kids).toEqual([['الصحيح', 'Sahih', true], ['الحسن', 'Hasan', true]])
  })

  it('gives each group its own hue', () => {
    const [a, b] = termsChart(glossary).branches
    expect(a.c.bar).toBeTruthy()
    expect(a.c).not.toBe(b.c)
  })

  it('is empty for an empty glossary', () => {
    expect(termsChart([]).branches).toEqual([])
  })

  it('carries nothing of the Map: only what the glossary names', () => {
    const chart = termsChart(glossary)
    const names = [chart.root.ar, ...chart.branches.flatMap((b) => [b.ar, ...b.kids.map((k) => k[0])])]
    expect(names.sort()).toEqual(['الحسن', 'الصحيح', 'الضعيف', 'المردود', 'المقبول', 'مصطلح الحديث'].sort())
  })

  it('is a config layoutChart accepts', () => {
    const L = layoutChart(termsChart(glossary))
    expect(L.branches).toHaveLength(2)
    expect(L.width).toBeGreaterThan(0)
  })
})

describe('branchChart', () => {
  it('roots one group and branches its terms, a term\'s kids under it', () => {
    const chart = branchChart(glossary, 0)
    expect(chart.root).toEqual({ ar: 'المقبول', en: 'Accepted' })
    expect(chart.branches.map((b) => b.ar)).toEqual(['الصحيح', 'الحسن'])
    expect(chart.branches[0].kids).toEqual([['لذاته', 'in itself', true], ['لغيره', 'by support', true]])
    expect(chart.branches[1].kids).toEqual([])
  })

  it('keeps the group\'s hue on its branches and lays out', () => {
    const chart = branchChart(glossary, 1)
    expect(chart.branches[0].c).toBe(termsChart(glossary).branches[1].c)
    expect(layoutChart(chart).branches).toHaveLength(1)
  })
})

describe('termAt', () => {
  it('finds a term and its group', () => {
    expect(termAt(glossary, 'الضعيف').group.title).toBe('Rejected')
  })

  it('finds a nested kid', () => {
    const found = termAt(glossary, 'لغيره')
    expect(found.term.en).toBe('by support')
    expect(found.group.title).toBe('Accepted')
  })

  it('is null for an unknown name', () => {
    expect(termAt(glossary, 'ؤ')).toBeNull()
  })
})
