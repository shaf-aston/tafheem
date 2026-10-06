/**
 * Where narrators are named inside a hadith's Arabic, as plain runs of text.
 *
 * The server sends `[start, end, id]` slices of the hadith's own `arabic`
 * string. The page draws that string in pieces (lib/hadithWords/saying drops
 * the direction marks and the quote marks), so a piece needs the slices that
 * fall inside it, counted from the piece's own start. Pure: no React.
 */
import HADITH from '../hadith.json'

import { MARKS, QUOTED, chainOf } from './hadithWords'

const { tones: TONES } = HADITH.narrator

/** The tone a grade wears: the first whose highest rank covers it, else danger. */
export const toneOf = (rank) => Object.entries(TONES).find(([, top]) => rank != null && rank <= top)?.[0] ?? 'danger'

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

/**
 * The hadith from the one who tells it on, with the chain before him dropped,
 * and `names` moved to match. The chain walker (chainOf) finds the cut by its
 * words; where it cannot, sunnah.com's own name links do: the last narrator
 * named before the speech opens is the teller. Neither finds one: whole.
 */
export function told(arabic, names) {
  const cut = chainOf(arabic)
  const before = names.filter(([, end]) => end <= arabic.search(QUOTED))
  const at = cut.chain
    ? arabic.lastIndexOf(cut.teller, arabic.length - cut.body.length)
    : (before.length > 1 ? Math.max(...before.map(([start]) => start)) : 0)
  return {
    text: arabic.slice(at),
    names: names.filter(([start]) => start >= at).map(([start, end, id]) => [start - at, end - at, id]),
  }
}
