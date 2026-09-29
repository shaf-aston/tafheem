import { describe, expect, it } from 'vitest'
import { chartTree, nodeAt, viewConfig } from './pbsTree'
import { CHARTS } from './pbsData'

const chart = CHARTS.find((c) => c.id === '05')

describe('pbsTree', () => {
  it('has the chart branches', () => {
    expect(chartTree(chart, {}).kids).toHaveLength(6)
  })
  it('falls back to SUB with empty English', () => {
    const t = chartTree(chart, {}, { '05.0.1': 'أ · ب' })
    const kid = nodeAt(t, [0, 1])
    expect(kid.kids.map((k) => [k.ar, k.en])).toEqual([['أ', ''], ['ب', '']])
    expect(kid.kids[0].c).toBe(t.kids[0].c)
  })
  it('deep overrides SUB and drops duplicate ar', () => {
    const t = chartTree(chart, { '05.0.1': [['س', 'x'], ['س', 'y']], '05.0.1.0': [['ص', 'z']] }, { '05.0.1': 'أ' })
    expect(nodeAt(t, [0, 1]).kids).toHaveLength(1)
    expect(nodeAt(t, [0, 1, 0, 0]).ar).toBe('ص')
  })
  it('returns null out of range', () => {
    expect(nodeAt(chartTree(chart, {}, {}), [99])).toBeNull()
  })
  it('viewConfig flags nodes with kids', () => {
    const v = viewConfig(chartTree(chart, {}, { '05.0.1': 'أ' }).kids[0])
    expect(v.branches[1].hasKids).toBe(true)
    expect(v.branches[0].hasKids).toBe(false)
  })
})
