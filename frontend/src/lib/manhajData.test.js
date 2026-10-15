import { describe, expect, it } from 'vitest'
import { FAMILIES, differs, sharedWith } from './manhajData'

describe('manhajData', () => {
  it('every group answers exactly its family questions', () => {
    for (const f of FAMILIES) {
      const qs = f.questions.map((q) => q.id).sort()
      for (const g of f.groups) {
        expect(Object.keys(g.positions).sort(), `${f.id}/${g.id}`).toEqual(qs)
        for (const [tag, text] of Object.values(g.positions)) {
          expect(tag && text, `${f.id}/${g.id}`).toBeTruthy()
        }
        expect(g.beliefs.length, g.id).toBeGreaterThan(0)
        expect(g.texts.length, g.id).toBeGreaterThan(0)
      }
    }
  })
  it('group ids are unique', () => {
    const ids = FAMILIES.flatMap((f) => f.groups.map((g) => g.id))
    expect(new Set(ids).size).toBe(ids.length)
  })
  it('compares by tag and ignores n/a', () => {
    const creed = FAMILIES.find((f) => f.id === 'creed')
    const by = (id) => creed.groups.find((g) => g.id === id)
    expect(differs(by('ashari'), by('maturidi'), 'ruya')).toBe(false)
    expect(differs(by('ashari'), by('mutazila'), 'ruya')).toBe(true)
    expect(differs(by('ashari'), by('jahmiyya'), 'imama')).toBeNull()
    expect(sharedWith(creed, by('ashari'), 'quran').map((g) => g.id)).toEqual(['maturidi'])
  })
})
