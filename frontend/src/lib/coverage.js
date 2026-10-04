/**
 * How much of the Qur'an the known words add up to.
 *
 * `words` is the word table, `coverage` is coverage.json (`total`, `lemmas`,
 * `counts`), `knownItems` are the meaningKeys the store calls known.
 *
 * Several words can share a meaningKey and an answer does not say which of them
 * was asked, so a known meaningKey credits ONE of its words: the one with the
 * fewest Qur'an words behind it, among those that are in the Qur'an at all (an
 * everyday word sharing the meaning would otherwise credit nothing). A lemma is
 * counted once however many known words use it.
 */
export function coverageOf(words, coverage, knownItems) {
  const known = new Set(knownItems)
  if (!known.size) return null

  const weight = (word) => (word.lemmas ?? []).reduce((sum, at) => sum + coverage.counts[at], 0)
  const cheapest = new Map()
  for (const word of words) {
    if (!known.has(word.meaningKey) || !word.lemmas) continue
    const best = cheapest.get(word.meaningKey)
    if (!best || weight(word) < weight(best)) cheapest.set(word.meaningKey, word)
  }

  const credited = new Set([...cheapest.values()].flatMap((word) => word.lemmas ?? []))
  let covered = 0
  for (const at of credited) covered += coverage.counts[at]
  return covered / coverage.total
}
