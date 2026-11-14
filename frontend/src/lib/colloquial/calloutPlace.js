/**
 * Where a tapped dot's label can stand, beside the dot, without covering the drawing.
 *
 * The picture's own box is never grown to make room. A figure (a body, a face, an
 * outfit) is narrower than its box, so there is empty margin on either side; the
 * label stands there, against the drawing, with a thin line back to its dot. A drawing
 * that fills its box (a house, a table, a map) has no margin, and this answers null: the
 * caller keeps the words in the card, where they always were.
 *
 * Pure, in pixels from the picture's top-left corner, so every rule here is checked
 * without a browser (calloutPlace.test.js). The caller measures the box, the drawing's
 * extent and the dots; this only chooses.
 *
 * Nothing is covered: not the drawing (the label is outside its extent), not any other
 * dot (each is given a halo), not any other dot's line out to its place, not its own dot.
 */

/** Room kept between the label and the drawing, and between the label and the box's edge. */
const GAP = 6
const EDGE = 2
/** Narrower than this and a word has to break mid-letter; wider adds length to the line for no gain. */
export const MIN_WIDTH = 56
export const MAX_WIDTH = 132
/** Clear air around every other dot, so a label never sits against one. */
const HALO = 4

const clamp = (n, lo, hi) => Math.min(Math.max(n, lo), hi)

const meets = (a, b) => a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1

const around = ({ x, y, r }, extra) => ({ x0: x - r - extra, y0: y - r - extra, x1: x + r + extra, y1: y + r + extra })

const spanOf = ({ x0, y0, x1, y1 }) => ({ x0: Math.min(x0, x1), y0: Math.min(y0, y1), x1: Math.max(x0, x1), y1: Math.max(y0, y1) })

/**
 * `box` {w, h}: the picture's box. `art` {x0, y0, x1, y1}: the drawing's extent.
 * `dot` {x, y, r}: the tapped dot. `height`: how tall the label stands (measured by the caller).
 * `others` [{x, y, r}] or [{x0, y0, x1, y1}]: every other dot (or area) that must stay uncovered.
 * `lines` [{x0, y0, x1, y1}]: every other dot's line out to its place.
 * Gives {side, x, y, w, line: {x, y}} (the label's left, top and width, and where the line meets it), or null.
 */
export function placeCallout({ box, art, dot, height, others = [], lines = [] }) {
  if (!box?.w || !box?.h || !art || !dot || !(height > 0) || height > box.h - EDGE * 2) return null

  const top = clamp(dot.y - height / 2, EDGE, box.h - height - EDGE)
  // Only the side the dot is nearer to: the far side would run the line across the whole figure.
  const side = dot.x < (art.x0 + art.x1) / 2 ? 'left' : 'right'

  const room = side === 'left' ? art.x0 - GAP - EDGE : box.w - art.x1 - GAP - EDGE
  const w = Math.min(MAX_WIDTH, Math.floor(room))
  if (w < MIN_WIDTH) return null
  const x = side === 'left' ? art.x0 - GAP - w : art.x1 + GAP
  const stand = { x0: x, y0: top, x1: x + w, y1: top + height }
  const covered = [around(dot, HALO), ...others.map((o) => ('r' in o ? around(o, HALO) : o)), ...lines.map(spanOf)]
    .some((o) => meets(stand, o))
  if (covered) return null
  return { side, x, y: top, w, line: { x: side === 'left' ? x + w : x, y: clamp(dot.y, top + 8, top + height - 8) } }
}
