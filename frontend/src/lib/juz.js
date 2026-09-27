/**
 * The thirty ajza': where each starts, and which one a place falls in.
 *
 * Pure. The start points are data/juz.json, a copy of the backend's juz file
 * cut down to what the Quran tab's picker needs; juz.test.js keeps them equal.
 */
import juz from '../data/juz.json'

export const JUZ_COUNT = juz.starts.length

/** Where juz `n` (1–30) starts, as `{ surah, ayah }`. */
export function juzStart(n) {
  const [surah, ayah] = juz.starts[n - 1]
  return { surah, ayah }
}

/** Which juz the ayah `surah:ayah` sits in: the last one starting at or before it. */
export function juzOf(surah, ayah) {
  let n = 1
  juz.starts.forEach(([s, a], i) => {
    if (s < surah || (s === surah && a <= ayah)) n = i + 1
  })
  return n
}
