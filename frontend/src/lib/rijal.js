/**
 * Where narrators are named inside a hadith's Arabic, as plain runs of text.
 *
 * The server sends `[start, end, id]` slices of the hadith's own `arabic`
 * string. The page draws that string in pieces (lib/hadithWords/saying drops
 * the direction marks and the quote marks), so a piece needs the slices that
 * fall inside it, counted from the piece's own start. Pure: no React.
 */
import HADITH from '../hadith.json'

import { MARKS, QUOTED, chainLinks } from './hadithWords'

const { tones: TONES, teller: TELLER } = HADITH.narrator

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
 * and `names` moved to match. The server's `cut` (data/hadith/chain.json) finds
 * the teller by the chain's words; with none, sunnah.com's own name links do:
 * the last narrator named before the speech opens is the teller. Neither: whole.
 */
export function told(arabic, cut, names) {
  const before = names.filter(([, end]) => end <= arabic.search(QUOTED))
  const at = cut ? cut[0] : (before.length >= TELLER ? Math.max(...before.map(([start]) => start)) : 0)
  return {
    text: arabic.slice(at),
    names: names.filter(([start]) => start >= at).map(([start, end, id]) => [start - at, end - at, id]),
  }
}

/**
 * A drawn chain (lib/hadithWords chainLinks of the Arabic before `cut`) with each
 * narrator's id where sunnah.com linked his name in this hadith: the slice
 * overlapping the place his name stands. A name it did not link stays plain.
 * Each name in the box is a `member` (a box may join several: أيوب، ويونس) with
 * its own words, cut to the box so an aside after it stays out, and its `note`
 * (a weak narrator, from usul.db, starting where his slice starts), for lib/weak.
 * The box carries the `ties` that start at any member: the links of the chain a
 * source puts in doubt, each saying who said the word before that name.
 */
export function linked(links, names, chain, notes = [], ties = []) {
  const add = (link) => {
    if (!link) return link
    const [from, to] = link.span ?? [0, 0]
    const slices = names.filter(([start, end]) => start < to && end > from)
    return {
      ...link, id: slices[0]?.[2] ?? null,
      members: slices.map(([start, end, id]) => ({
        id, name: chain.slice(Math.max(start, from), Math.min(end, to)), note: notes.find((n) => n.at === start) ?? null,
      })),
      ties: ties.filter((t) => slices.some(([start]) => t.at === start)),
    }
  }
  return {
    main: links.main.map(add),
    branches: links.branches.map((b) => ({ ...b, links: b.links.map(add), join: add(b.join) })),
  }
}

/**
 * The chain drawing for one hadith, its names linked. `cut` is the server's [teller_at, body_at]
 * (backend/services/hadith/chain, the one cutter; offsets assume no character outside the BMP),
 * `names` its own slices, `notes` its weak narrators, `ties` its doubtful links.
 */
export function drawnChain(arabic, cut, names, notes = [], ties = []) {
  const chain = arabic.slice(0, cut[1]).trim()
  const at = arabic.indexOf(chain)
  const moved = (list) => list.map((n) => ({ ...n, at: n.at - at }))
  return linked(chainLinks(chain), names.map(([start, end, id]) => [start - at, end - at, id]), chain, moved(notes), moved(ties))
}
