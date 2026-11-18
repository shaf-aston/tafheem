/**
 * Where a picture board's tapped place says its word: in a rail on the drawing's right.
 *
 * Every board is drawn in its own units (`view`, [x, y, w, h]). The picture shows that view
 * widened by a rail (`railView`), empty space the drawing never reaches, so a word standing
 * there covers nothing, on any kind of board: a figure, a house, a map, a grid of tiles.
 * The word stands level with its place (`anchorOf`: a dot's centre, an area's right edge),
 * joined to it by a thin line, clamped to stay inside the picture.
 *
 * Pure, in the board's own units, so it is the same rule for every board and needs no
 * measuring of the drawing; the caller only says how tall the label came out.
 */
import settings from '../../config/colloquial-display.json'

export const RAIL = settings['label-rail']
// Space between the drawing and the label, and the label and the rail's far edge: a share of the rail.
const GAP = 0.06

// The least height of the picture, as a share of its width: a strip of tiles (the days of the week) is
// shorter than a label, so the picture is given room below it for the rail to hold one.
export const LEAST_TALL = 0.32

/** The board's view with the rail added on its right, no shorter than a label needs: `least` is the shown
 * label's height in the board's units, so a short board (a strip, a map) grows room below it for a tall
 * label on a narrow phone. The width never depends on it, so the scale does not either. */
export const railView = ([x, y, w, h], least = 0) => [x, y, w * (1 + RAIL), Math.max(h, w * (1 + RAIL) * LEAST_TALL, least)]

/** The point a place's word is joined to: a dot's centre, or the middle of an area's right edge. */
export const anchorOf = (spot) => (spot.area
  ? { x: spot.area[0] + spot.area[2], y: spot.area[1] + spot.area[3] / 2 }
  : { x: spot.x, y: spot.y })

const clamp = (n, lo, hi) => Math.min(Math.max(n, lo), Math.max(lo, hi))

/**
 * The label's box and its line's end, in the board's units. `height`: the label's height in those
 * units (its measured height over the picture's scale). Gives { x, y, w, line: { x, y } }.
 */
export function placeInRail(view, spot, height = 0) {
  const [vx, vy, vw] = view
  const vh = railView(view, height)[3]
  const rail = vw * RAIL
  const gap = rail * GAP
  const anchor = anchorOf(spot)
  const x = vx + vw + gap
  const y = clamp(anchor.y - height / 2, vy, vy + vh - height)
  return { x, y, w: rail - 2 * gap, line: { x, y: clamp(anchor.y, y + Math.min(height / 2, 4), y + height - Math.min(height / 2, 4)) } }
}
