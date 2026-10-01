/**
 * The shape of a vine on Grow's map. Things on a vine wind like a snake: left
 * to right, a curl down, right to left, so however narrow the space the vine
 * never breaks and never scrolls sideways. Pure: widths in, positions and an
 * SVG path out; components/grow/Vine.jsx draws them.
 */

/** Where the k-th of n things sits: columns fill the width, odd rows run back, and a short row spreads out no wider than `spread` cells each. */
export function snake(n, width, { cell, row, top, sway, spread }) {
  const cols = Math.max(1, Math.min(n, Math.floor(width / cell)))
  const cw = Math.min(width / cols, cell * spread)
  const spots = Array.from({ length: n }, (_, k) => {
    const r = Math.floor(k / cols)
    const c = r % 2 ? cols - 1 - (k % cols) : k % cols
    return { x: c * cw + cw / 2, y: r * row + top + (k % 2 ? sway : -sway), r }
  })
  return { spots, cw, height: Math.ceil(n / cols) * row }
}

/** One smooth path through the spots, curling round at each row's end. `from` starts it at the left edge. */
export function vinePath(spots, cw, from = false) {
  if (!spots.length) return ''
  const [first] = spots
  let d = from ? `M0 ${first.y}L${first.x} ${first.y}` : `M${first.x} ${first.y}`
  spots.slice(1).forEach((to, k) => {
    const at = spots[k]
    if (to.r === at.r) {
      const mid = (at.x + to.x) / 2
      d += `C${mid} ${at.y} ${mid} ${to.y} ${to.x} ${to.y}`
    } else {
      const out = (at.r % 2 ? -1 : 1) * cw * 0.55
      d += `C${at.x + out} ${at.y} ${to.x + out} ${to.y} ${to.x} ${to.y}`
    }
  })
  return d
}
