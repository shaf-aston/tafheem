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
  if (!knownItems.length) return null
  let covered = 0
  for (const at of credited(words, coverage, knownItems)) covered += coverage.counts[at]
  return covered / coverage.total
}

/**
 * The same share per surah, from surah_coverage.json (`total`, `counts` keyed
 * by lemma index). Credits the same lemmas as the whole meter, so the two agree.
 */
export function surahShares(words, coverage, knownItems, bySurah) {
  const lemmas = credited(words, coverage, knownItems)
  return bySurah.map(({ total, counts }) => {
    let covered = 0
    for (const at of lemmas) covered += counts[at] ?? 0
    return covered / total
  })
}

/** The lemmas the known meaningKeys credit, by the rule above. */
function credited(words, coverage, knownItems) {
  const known = new Set(knownItems)
  const weight = (word) => (word.lemmas ?? []).reduce((sum, at) => sum + coverage.counts[at], 0)
  const cheapest = new Map()
  for (const word of words) {
    if (!known.has(word.meaningKey) || !word.lemmas) continue
    const best = cheapest.get(word.meaningKey)
    if (!best || weight(word) < weight(best)) cheapest.set(word.meaningKey, word)
  }
  return new Set([...cheapest.values()].flatMap((word) => word.lemmas))
}

/**
 * A share as a percent figure: whole from 10% up, one decimal below, where a
 * small share is news. Under a tenth of a percent says so rather than round a
 * known word down to 0%.
 */
export function shareOf(fraction, language) {
  const format = (n, digits) => new Intl.NumberFormat(language, { maximumFractionDigits: digits }).format(n)
  if (fraction === 0) return format(0, 0)
  if (fraction < 0.001) return `<${format(0.1, 1)}`
  return format(fraction * 100, fraction >= 0.1 ? 0 : 1)
}
