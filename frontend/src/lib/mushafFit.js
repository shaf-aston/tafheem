/**
 * How big one printed page is drawn (components/quran/MushafPage). A page keeps
 * the print's lines, so it cannot wrap: it takes one font size for every line,
 * the largest at which its widest line still fits, and the lines spread to the
 * edges (justified) as the print's do. Pure: widths in, a size out.
 *
 * `natural` is each ayah line's width at `measure` px; `width` is the page's.
 * A page with nothing measured yet (no font, no box) gets null and is drawn at
 * the reading size until it can be measured.
 */
export function pageFontPx(natural, width, { measure, fill }) {
  const widest = Math.max(0, ...natural)
  if (!widest || !width) return null
  return Math.floor((width * fill / widest) * measure * 10) / 10
}

/** The first two pages are framed and short, their lines set in the middle. */
export const isCentred = (page) => page <= 2

/** An ayah's words on one line, split as the print writes them. */
export const wordsOf = (text) => text.split(' ')
