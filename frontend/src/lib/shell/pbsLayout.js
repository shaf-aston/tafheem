/**
 * Where every box and line of a PBS chart goes, drawn only.
 *
 * Pure: no DOM, no React, no colour decisions beyond passing each branch's own
 * `c` through. Geometry is the same across every science (config/pbsChart.json), so it
 * lives once here rather than being recomputed per chart. A box is as wide as its level
 * says and as tall as its words need: the Arabic name and its English wrap to the box
 * (lib/shell/pbsFit) and the box grows to hold the lines, so no label ever leaves its
 * box. The branches share one height (they hang from one bus), and a branch's kids stack
 * by their own heights.
 *
 * `measure(text, weight)` is a run's width in ems: the browser's real font
 * (lib/shell/useTextMeasure), or the estimate without one. The chart's width does not
 * depend on it, only its heights. A chart is never narrower than its root box: with
 * one branch the column stands centred under it, with none the root stands alone.
 */
import knobs from '../../config/pbsChart.json'
import { estimate, fitLabel } from './pbsFit'

const { margin: M, levels } = knobs
const COLW = knobs['column-width']
const PITCH = COLW + knobs['column-gap']
const HALF = COLW / 2

/** The drawing's width for `n` branches: its columns, never less than the root box. The words do not change it. */
const widthFor = (n) => M * 2 + Math.max(n * COLW + (n - 1) * knobs['column-gap'], levels.root.width)

/** The smallest label any chart draws, in drawing units: a chart shown at 1:1 has its smallest words this many px. */
export const SMALLEST_LABEL = Math.min(...Object.values(levels).map((level) => level['sub-size']))

/** The px width a chart needs for its smallest label to draw at `px`. */
export const widthAtLabel = (config, px) => Math.ceil((widthFor(config.branches.length) * px) / SMALLEST_LABEL)

const BOLD = 700
const REGULAR = 400
const roughly = (text) => estimate(text)

/** A label's words set for a box of `level` (`hint`: a › sits at its left): the lines of its name and of its English, and the height they take. */
function set(level, ar, en, hint, measure) {
  const room = level.width - 2 * (hint ? knobs['hint-pad'] : knobs.pad)
  const name = fitLabel(ar, { room, size: level.size }, (t) => measure(t, BOLD))
  const sub = en ? fitLabel(`(${en})`, { room, size: level['sub-size'] }, (t) => measure(t, REGULAR)) : null
  const nameH = name.lines.length * name.size * knobs.line
  const subH = sub ? sub.lines.length * sub.size * knobs['sub-line'] + knobs['sub-gap'] : 0
  return { name, sub, nameH, subH, height: Math.max(level.height, Math.ceil(nameH + subH + 2 * knobs['pad-y'])) }
}

/** The lines' baselines for a box at `top` and `height`: the name over its English, together centred in the box. */
function place({ name, sub, nameH, subH }, top, height) {
  const line = (size, pitch, from) => (text, i) => ({ text, y: from + i * pitch + (pitch + size * 2 * knobs.drop) / 2 })
  const start = top + (height - nameH - subH) / 2
  const namePitch = name.size * knobs.line
  const subFrom = start + nameH + knobs['sub-gap']
  const subPitch = sub ? sub.size * knobs['sub-line'] : 0
  return {
    size: name.size,
    lines: name.lines.map(line(name.size, namePitch, start)),
    sub: sub && { size: sub.size, lines: sub.lines.map(line(sub.size, subPitch, subFrom)) },
  }
}

/** Every position and connector a chart's SVG needs, computed once per render. */
export function layoutChart(config, measure = roughly) {
  const { branches } = config
  const n = branches.length
  const columns = Math.max(0, n * COLW + (n - 1) * knobs['column-gap'])
  const width = widthFor(n)
  const colX = (i) => (width - columns) / 2 + i * PITCH
  const rootCx = width / 2

  const rootSet = set(levels.root, config.root.ar, config.root.en, false, measure)
  const rootY = knobs['root-top']
  const rootBottom = rootY + rootSet.height
  const bus = rootBottom + knobs['root-to-bus']
  const branchY = bus + knobs['bus-to-branch']

  // The branches hang from one bus: they share the tallest one's height.
  const branchSets = branches.map((b) => set(levels.branch, b.ar, b.en, b.hasKids && !b.leaf, measure))
  const branchH = Math.max(0, ...branchSets.map((s) => s.height))
  const kidY = branchY + branchH + knobs['branch-to-kid']

  let bottom = n ? branchY + branchH : rootBottom
  const laid = branches.map((b, i) => {
    const x = colX(i), cx = x + HALF, spine = x + 8, kx = x + knobs['kid-indent']
    let y = kidY
    const kids = b.kids.map((k, j) => {
      const s = set(levels.kid, k[0], k[1], Boolean(k[2] && !k[3]), measure)
      const top = y
      y += s.height + knobs['kid-gap']
      const cy = top + s.height / 2
      return {
        kid: k,
        j,
        box: { x: kx, y: top, w: levels.kid.width, h: s.height, cx: kx + levels.kid.width / 2, hint: Boolean(k[2] && !k[3]), label: place(s, top, s.height) },
        connectorPath: `M${spine},${cy} H${kx}`,
      }
    })
    if (kids.length) bottom = Math.max(bottom, y - knobs['kid-gap'])
    const last = kids.at(-1)
    return {
      branch: b,
      i,
      box: { x: x + 8, y: branchY, w: levels.branch.width, h: branchH, cx, hint: b.hasKids && !b.leaf, label: place(branchSets[i], branchY, branchH) },
      stemPath: `M${cx},${bus} V${branchY}`,
      spinePath: last && `M${cx},${branchY + branchH} V${branchY + branchH + knobs['branch-drop']} H${spine} V${last.box.y + last.box.h / 2}`,
      kids,
    }
  })

  const rule = bottom + knobs['rule-gap']
  const notes = config.footnote.length
  return {
    width,
    height: notes ? rule + knobs['line-pitch'] * notes + knobs['end-pad'] : bottom + knobs['end-pad'],
    rule: notes ? rule : null,
    root: { cx: rootCx, x: rootCx - levels.root.width / 2, y: rootY, w: levels.root.width, h: rootSet.height, label: place(rootSet, rootY, rootSet.height) },
    bus,
    busPath: n ? `M${colX(0) + HALF},${bus} H${colX(n - 1) + HALF}` : '',
    trunkPath: n ? `M${rootCx},${rootBottom} V${bus}` : '',
    branches: laid,
  }
}
