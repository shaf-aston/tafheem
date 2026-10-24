import { describe, expect, it } from 'vitest'

import knobs from '../../config/pbsChart.json'
import { CHARTS } from './pbsData'
import { layoutChart } from './pbsLayout'
import { chartTree, viewConfig } from './pbsTree'

const { levels } = knobs
const wide = (text) => text.length * 0.8 // a face far wider than the estimate: nearly everything has to wrap

/** Every view the Map can show: each science's whole chart, and every box with kids opened as the root. */
function* views() {
  for (const chart of CHARTS) {
    const walk = function* (node, path) {
      yield [`${chart.id}/${path.join('/')}`, viewConfig(node, path.length ? [] : chart.config.footnote)]
      for (const [i, kid] of node.kids.entries()) if (kid.kids.length) yield* walk(kid, [...path, i])
    }
    yield* walk(chartTree(chart), [])
  }
}

const boxes = (L) => [
  { level: 'root', box: L.root },
  ...L.branches.flatMap(({ box, kids }) => [{ level: 'branch', box }, ...kids.map((k) => ({ level: 'kid', box: k.box }))]),
]

describe('layoutChart', () => {
  it.each([['the estimate', undefined], ['a wide face', wide]])('keeps every label inside its box, with %s', (_, measure) => {
    for (const [at, config] of views()) {
      const L = layoutChart(config, measure)
      for (const { level, box } of boxes(L)) {
        const { label } = box
        const room = levels[level].width - 2 * (box.hint ? knobs['hint-pad'] : knobs.pad)
        const lines = [...label.lines.map((l) => ({ ...l, size: label.size })), ...(label.sub?.lines ?? []).map((l) => ({ ...l, size: label.sub.size }))]
        expect(lines.length, at).toBeGreaterThan(0)
        for (const line of lines) {
          // A line's height spans its size above the baseline and a third below it.
          expect(line.y - line.size, `${at} ${line.text} top`).toBeGreaterThanOrEqual(box.y)
          expect(line.y + line.size / 3, `${at} ${line.text} bottom`).toBeLessThanOrEqual(box.y + box.h)
        }
        const widest = Math.max(...label.lines.map((l) => (measure ?? ((t) => t.replace(/[ً-ٰٟ]/g, '').length * knobs['glyph-em']))(l.text) * label.size))
        expect(widest, `${at} ${label.lines[0].text}`).toBeLessThanOrEqual(room + 0.01)
      }
    }
  })

  it('never makes a box smaller than its level, and grows one only for words that need it', () => {
    const config = { root: { ar: 'جذر', en: 'Root' }, footnote: [], branches: [
      { ar: 'قصير', en: 'Short', c: {}, kids: [['قصير', 'Short'], ['كلمات كثيرة جدا في اسم واحد طويل لا يكاد ينتهي أبدا', 'A very long name that wraps across several lines of the box']] },
    ] }
    const [{ kids, box }] = layoutChart(config).branches
    expect(box.h).toBe(levels.branch.height)
    expect(kids[0].box.h).toBe(levels.kid.height)
    expect(kids[1].box.h).toBeGreaterThan(levels.kid.height)
  })

  it('hangs the branches from one bus at one height, and stacks a branch kids without overlap', () => {
    for (const [at, config] of views()) {
      const L = layoutChart(config, wide)
      expect(new Set(L.branches.map((b) => b.box.y)).size, at).toBe(1)
      expect(new Set(L.branches.map((b) => b.box.h)).size, at).toBe(1)
      for (const { kids, box } of L.branches) {
        let top = box.y + box.h
        let gap = knobs['branch-to-kid']
        for (const { box: kid } of kids) {
          expect(kid.y, at).toBeGreaterThanOrEqual(top + gap - 0.01)
          top = kid.y + kid.h
          gap = knobs['kid-gap']
        }
        expect(top, at).toBeLessThanOrEqual(L.height)
      }
    }
  })

  it('draws the footnote rule only when there is a footnote, and the chart closes under its lowest box', () => {
    const base = { root: { ar: 'جذر', en: '' }, branches: [{ ar: 'أ', en: '', c: {}, kids: [['ب', '']] }, { ar: 'ج', en: '', c: {}, kids: [] }] }
    const bare = layoutChart({ ...base, footnote: [] })
    const noted = layoutChart({ ...base, footnote: ['one', 'two'] })
    expect(bare.rule).toBeNull()
    expect(noted.rule).toBeGreaterThan(0)
    expect(noted.height).toBe(noted.rule + 2 * knobs['line-pitch'] + knobs['end-pad'])
    const lowest = bare.branches[0].kids[0].box
    expect(bare.height).toBe(lowest.y + lowest.h + knobs['end-pad'])
  })

  it('is never narrower than its root box: a lone column stands centred, and no branches leave the root alone', () => {
    const root = { ar: 'جذر', en: 'Root' }
    const one = layoutChart({ root, footnote: [], branches: [{ ar: 'أ', en: '', c: {}, kids: [['ب', '']] }] })
    expect(one.root.x).toBeGreaterThanOrEqual(0)
    expect(one.width).toBe(2 * knobs.margin + levels.root.width)
    expect(one.branches[0].box.cx).toBeCloseTo(one.root.cx)
    const none = layoutChart({ root, footnote: [], branches: [] })
    expect(none.root.x).toBeGreaterThanOrEqual(0)
    expect(none.trunkPath + none.busPath).toBe('')
    expect(Number.isFinite(none.height)).toBe(true)
    expect(none.height).toBeGreaterThan(none.root.y + none.root.h)
  })

  it('does not let wrapping change the chart width', () => {
    for (const [at, config] of views()) expect(layoutChart(config, wide).width, at).toBe(layoutChart(config).width)
  })

  it('centres a name that has no English in its box', () => {
    const config = { root: { ar: 'جذر', en: '' }, footnote: [], branches: [{ ar: 'اسم', en: '', c: {}, kids: [] }] }
    const { box } = layoutChart(config).branches[0]
    const [{ y }] = box.label.lines
    const middle = y - box.label.size * knobs.drop
    expect(Math.abs(middle - (box.y + box.h / 2))).toBeLessThan(0.01)
  })
})
