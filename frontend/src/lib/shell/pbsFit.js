/**
 * How a label is set in its box, pure: its words broken into lines that fit, and the size it is drawn at.
 *
 * `width(text)` is how wide a run of text draws, in ems, from the caller: the real font's measure in the browser
 * (lib/shell/useTextMeasure), an estimate where there is none (`estimate`). This file knows no font and no box.
 */
import knobs from '../../config/pbsChart.json'

const MARKS = /[ً-ٰٟۖ-ۭ]/g // vowel and recitation signs sit on a letter and add no width

/** A run's width in ems from its letter count alone: close enough to place boxes before the font is there. */
export const estimate = (text) => text.replace(MARKS, '').length * knobs['glyph-em']

/** The words split greedily: a line takes the next word while it still fits `room` (ems); a word wider than that stands alone. */
function greedy(words, room, width) {
  const lines = []
  let line = ''
  for (const word of words) {
    const joined = line ? `${line} ${word}` : word
    if (line && width(joined) > room) {
      lines.push(line)
      line = word
    } else line = joined
  }
  if (line) lines.push(line)
  return lines
}

const BALANCE_STEPS = 10

/**
 * The text as the fewest lines that fit `room`, and of those the most even (the narrowest room that still needs
 * no more lines), so a centred two-line label is not a long line over a stray word.
 */
export function wrap(text, room, width) {
  const words = text.split(/\s+/).filter(Boolean)
  const lines = greedy(words, room, width)
  if (lines.length < 2) return lines
  let low = Math.max(...words.map(width))
  let high = room
  for (let i = 0; i < BALANCE_STEPS && low < high; i += 1) {
    const mid = (low + high) / 2
    if (greedy(words, mid, width).length === lines.length) high = mid
    else low = mid
  }
  return greedy(words, high, width)
}

/**
 * A label set in a box `room` wide: `{ lines, size }`. It wraps rather than shrinks; only a single word wider than
 * the room (which no wrapping can help) is drawn smaller, just enough to fit.
 */
export function fitLabel(text, { room, size }, width) {
  const lines = wrap(text, room / size, width)
  const widest = Math.max(0, ...lines.map(width)) * size
  return { lines, size: widest > room ? (size * room) / widest : size }
}

/** Every Arabic name a chart draws, root to kids: the words its font has to be able to draw before the boxes can be sized. */
export const namesOf = ({ root, branches }) => [root.ar, ...branches.flatMap((b) => [b.ar, ...b.kids.map((k) => k[0])])].join(' ')
