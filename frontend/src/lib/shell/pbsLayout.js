/**
 * Where every box and line of a PBS chart goes, drawn only.
 *
 * Pure: no DOM, no React, no colour decisions beyond passing each branch's own
 * `c` through. Geometry is fixed and identical across every science, so it
 * lives once here rather than being recomputed per chart.
 */
const M = 18, COLW = 236, GAP = 16, PITCH = 252
const ROOT_Y = 40, ROOT_H = 66, BR_Y = 162, BR_H = 58
const KID_Y = 248, KID_H = 46, KID_PITCH = 58

/** Every position and connector a chart's SVG needs, computed once per render. */
export function layoutChart(config) {
  const branches = config.branches
  const n = branches.length
  const width = M * 2 + n * COLW + (n - 1) * GAP
  const maxKids = Math.max(...branches.map((b) => b.kids.length))
  const rule = KID_Y + (maxKids - 1) * KID_PITCH + KID_H + 32
  const height = rule + 18 * config.footnote.length + 30
  const colX = (i) => M + i * PITCH
  const rootCx = width / 2
  const bus = ROOT_Y + ROOT_H + 26

  return {
    width,
    height,
    rule,
    root: { cx: rootCx, x: rootCx - 180, y: ROOT_Y, w: 360, h: ROOT_H, textY: ROOT_Y + 34, subTextY: ROOT_Y + 54 },
    bus,
    busPath: `M${colX(0) + 118},${bus} H${colX(n - 1) + 118}`,
    trunkPath: `M${rootCx},${ROOT_Y + ROOT_H} V${bus}`,
    branches: branches.map((b, i) => {
      const x = colX(i), cx = x + 118, spine = x + 8, kx = x + 34, kw = 196
      const lastCy = KID_Y + (b.kids.length - 1) * KID_PITCH + KID_H / 2
      return {
        branch: b,
        i,
        box: { x: x + 8, y: BR_Y, w: 220, h: BR_H, cx, textY: BR_Y + 26, subTextY: BR_Y + 45 },
        stemPath: `M${cx},${bus} V${BR_Y}`,
        spinePath: `M${cx},${BR_Y + BR_H} V${BR_Y + BR_H + 16} H${spine} V${lastCy}`,
        kids: b.kids.map((k, j) => {
          const y = KID_Y + j * KID_PITCH, cy = y + KID_H / 2
          return {
            kid: k,
            j,
            box: { x: kx, y, w: kw, h: KID_H, cx: kx + kw / 2, textY: y + 22, subTextY: y + 37 },
            connectorPath: `M${spine},${cy} H${kx}`,
          }
        }),
      }
    }),
  }
}
