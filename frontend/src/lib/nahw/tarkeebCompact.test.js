import { describe, expect, it } from 'vitest'
import { compact, groupText } from './tarkeebCompact'

// وَالكِتَابُ is written as one word but cut into two pieces; فِيهِ is a خبر made of
// two pieces (a join of its own); يَكْتُبُهُ is named as its own first piece (no join);
// the hidden doer is never written.
const TARKEEB = {
  words: ['وَـ', 'الكِتَابُ', 'فِيهِ', 'هُوَ', 'يَكْتُبُهُ'],
  written: ['وَالكِتَابُ', 'وَالكِتَابُ', 'فِيهِ', 'هُوَ', 'يَكْتُبُهُ'],
  tree: {
    label: 'جُمْلَةٌ',
    children: [
      { word: 0, role: 'حرف عطف', tone: 'harf', children: [], parts: [] },
      {
        label: 'جُمْلَةٌ اِسْمِيَّةٌ', role: 'معطوفة', tone: 'jumla', parts: [],
        children: [
          { word: 1, role: '؟ لم يحلل', gap: true, children: [], parts: [] },
          { word: 2, role: 'خبر', tone: 'khabar', children: [], parts: [{ role: 'حرف جر', tone: 'harf' }, { role: 'مجرور', tone: 'majrur', pronoun: 'هو' }] },
        ],
      },
      { word: 3, role: 'فاعل', tone: 'fail', hidden: true, children: [], parts: [] },
      { word: 4, role: 'فعل', tone: 'fil', children: [], parts: [{ role: 'فعل', tone: 'fil' }, { role: 'فاعل', tone: 'fail' }, { role: 'مفعول به', tone: 'maful' }] },
    ],
    parts: [],
  },
}
const layout = compact(TARKEEB)
const roles = (i) => layout.columns[i].names.map((n) => n.role)

describe('compact', () => {
  it('writes each word\'s own name straight under it', () => {
    expect(layout.columns.map((c) => c.word)).toEqual(TARKEEB.words)
    expect(roles(0)).toEqual(['حرف عطف'])
    expect(layout.columns[0].tone).toBe('harf')
  })

  it('writes a word\'s pieces side by side, with the pronoun they stand for', () => {
    expect(roles(2)).toEqual(['حرف جر', 'مجرور'])
    expect(layout.columns[2].names[1].pronoun).toBe('هو')
    expect(roles(4)).toEqual(['فعل', 'فاعل', 'مفعول به'])
  })

  it('marks a word not yet named as a gap', () => {
    expect(layout.columns[1].names).toEqual([expect.objectContaining({ role: '؟', tone: 'gap' })])
    expect(layout.columns[1].tone).toBe('gap')
  })

  it('draws one brace per join, a word whose pieces make up another job included', () => {
    const braces = layout.groups.map((g) => [g.from, g.to, g.level, g.role ?? g.label])
    expect(braces).toEqual([[0, 4, 3, 'جُمْلَةٌ'], [1, 2, 2, 'معطوفة'], [2, 2, 1, 'خبر']])
    expect(layout.depth).toBe(3)
  })

  it('gives no brace to a word named as its own first piece', () => {
    expect(layout.groups.some((g) => g.from === 4)).toBe(false)
  })

  it('joins a cut word back into one span and counts only written words', () => {
    expect(layout.spans).toEqual([
      { from: 0, to: 1, text: 'وَالكِتَابُ', nth: 0, hidden: false },
      { from: 2, to: 2, text: 'فِيهِ', nth: 1, hidden: false },
      { from: 3, to: 3, text: 'هُوَ', nth: -1, hidden: true },
      { from: 4, to: 4, text: 'يَكْتُبُهُ', nth: 2, hidden: false },
    ])
    expect(layout.columns[3].hidden).toBe(true)
  })

  it('writes no name under a word the tree gave none', () => {
    const bare = compact({ words: ['،'], tree: { label: 'جُمْلَةٌ', children: [{ word: 0, children: [], parts: [] }], parts: [] } })
    expect(bare.columns[0].names).toEqual([])
  })

  it('treats every column as whole when the words are not cut', () => {
    expect(compact({ ...TARKEEB, written: undefined }).spans).toHaveLength(5)
  })
})

describe('groupText', () => {
  it('reads the written words a brace covers, leaving out the hidden ones', () => {
    expect(groupText(layout, layout.groups[0])).toBe('وَالكِتَابُ فِيهِ يَكْتُبُهُ')
    expect(groupText(layout, layout.groups[2])).toBe('فِيهِ')
  })
})
