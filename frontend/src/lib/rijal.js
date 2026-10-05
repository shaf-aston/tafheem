/**
 * Where narrators are named inside a hadith's Arabic, as plain runs of text.
 *
 * The server sends `[start, end, id]` slices of the hadith's own `arabic`
 * string. The page draws that string in pieces (lib/hadithWords/saying drops
 * the direction marks and the quote marks), so a piece needs the slices that
 * fall inside it, counted from the piece's own start. Pure: no React.
 */
import { MARKS } from './hadithWords'

/**
 * `text` split into `{text}` and `{text, id}` runs. `offset` is where `text`
 * begins in the whole hadith; a slice not wholly inside it is ignored.
 */
export function runs(text, names, offset = 0) {
  const out = []
  let at = 0
  for (const [start, end, id] of [...names].sort((a, b) => a[0] - b[0])) {
    const from = start - offset
    const to = end - offset
    if (from < at || to <= from || to > text.length) continue
    if (from > at) out.push({ text: text.slice(at, from) })
    out.push({ text: text.slice(from, to), id })
    at = to
  }
  if (at < text.length) out.push({ text: text.slice(at) })
  return out
}

/** `names` moved from offsets in `text` to offsets in `text` with its direction marks removed. */
export const withoutMarks = (text, names) =>
  names.map(([start, end, id]) => {
    const dropped = (to) => (text.slice(0, to).match(MARKS) ?? []).length
    return [start - dropped(start), end - dropped(end), id]
  })
