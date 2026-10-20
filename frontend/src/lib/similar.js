/**
 * Similar verses (mutashabihat): pure helpers, no screen and no network.
 *
 * The backend marks where two twin verses differ as spans of word positions,
 * [start, end) over the ayah split on whitespace. The page works per word, so
 * spans become one flag per word here and nowhere else.
 */
import surahs from '../data/surahs.json'

/** One true/false per word: is it inside any span. Spans may overlap or run past the end. */
export function wordFlags(count, spans = []) {
  const flags = Array(count).fill(false)
  for (const [start, end] of spans) {
    for (let w = Math.max(0, start); w < Math.min(count, end); w += 1) flags[w] = true
  }
  return flags
}

/** Every ayah key ("2:59") that sits in some group, from a surah's groups. */
export const twinKeys = (groups = []) => new Set(groups.flatMap((group) => group.keys))

const nameOf = (key) => surahs.find((s) => s.n === Number(key.split(':')[0]))?.en ?? key

/** Where the two verses are, in plain words. */
export function placeLine(mine, theirs) {
  const [mineSurah, mineAyah] = mine.split(':')
  const [theirSurah, theirAyah] = theirs.split(':')
  return mineSurah === theirSurah
    ? `Both are in Surah ${nameOf(mine)}, this one is ayah ${mineAyah}, that one ayah ${theirAyah}`
    : `This one is in Surah ${nameOf(mine)}, that one in Surah ${nameOf(theirs)}`
}
