import { describe, expect, it } from 'vitest'
import { nodeAt, viewConfig } from './pbsTree'
import { CHARTS, HUE } from './pbsData'

const chart = CHARTS.find((c) => c.id === '04')

/** Every node of every science, with where it sits, so a defect names its place. */
function* nodes(node, where) {
  yield [node, where]
  for (const [i, kid] of node.kids.entries()) yield* nodes(kid, `${where}/${i}`)
}

describe('pbs data', () => {
  it('holds the nine sciences, in order', () => {
    expect(CHARTS.map((c) => c.id)).toEqual(['01', '02', '03', '04', '05', '06', '07', '08', '09'])
  })
  it('names a real colour for every science and branch, and every box inherits its branch', () => {
    for (const c of CHARTS) {
      expect(c.accent, c.id).toBeTruthy()
      for (const branch of c.tree.kids) {
        expect(Object.values(HUE), `${c.id}/${branch.ar}`).toContain(branch.c)
        for (const [node, where] of nodes(branch, '')) expect(node.c, `${c.id}${where}`).toBe(branch.c)
      }
    }
  })
  it('gives every box Arabic and never repeats a sibling', () => {
    for (const c of CHARTS) {
      for (const [node, where] of nodes(c.tree, '')) {
        expect(node.ar, `${c.id}${where}`).toBeTruthy()
        const ars = node.kids.map((k) => k.ar)
        expect(new Set(ars).size, `${c.id}${where} repeats a sibling`).toBe(ars.length)
      }
    }
  })
})

describe('pbsTree', () => {
  it('has the chart branches', () => {
    expect(chart.tree.kids).toHaveLength(6)
  })
  it('finds a node by its path and returns null out of range', () => {
    expect(nodeAt(chart.tree, [0, 1])).toBe(chart.tree.kids[0].kids[1])
    expect(nodeAt(chart.tree, [])).toBe(chart.tree)
    expect(nodeAt(chart.tree, [99])).toBeNull()
    expect(nodeAt(chart.tree, [0, 99, 0])).toBeNull()
  })
  it('viewConfig flags nodes with kids', () => {
    const node = { ar: 'ج', en: '', kids: [{ ar: 'أ', en: '', c: 1, kids: [{ ar: 'ب', en: '', c: 1, kids: [] }] }, { ar: 'ت', en: '', c: 1, kids: [] }] }
    const v = viewConfig(node, ['note'])
    expect(v.branches.map((b) => b.hasKids)).toEqual([true, false])
    expect(v.branches[0].kids).toEqual([['ب', '', false]])
    expect(v.footnote).toEqual(['note'])
  })
})
