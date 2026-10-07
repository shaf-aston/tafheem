/**
 * How much of the Qur'an the known words add up to.
 *
 * `words` is the word table, `coverage` is coverage.json (`total`, `lemmas`,
 * `counts`), `learnt` are the summary rows the store calls known (learntOf).
 *
 * Several words can share a meaningKey, so a learnt meaning credits the words
 * answered right through it (`row.words`). An answer saved before those were
 * kept names none; then it credits ONE word: the one with the fewest Qur'an
 * words behind it, among those in the Qur'an at all. A lemma is counted once
 * however many learnt words use it.
 */
export function coverageOf(words, coverage, learnt) {
  if (!learnt.length) return null
  let covered = 0
  for (const at of credited(words, coverage, learnt)) covered += coverage.counts[at]
  return covered / coverage.total
}

/**
 * The same share per surah, from surah_coverage.json (`total`, `counts` keyed
 * by lemma index). Credits the same lemmas as the whole meter, so the two agree.
 */
export function surahShares(words, coverage, learnt, bySurah) {
  const lemmas = credited(words, coverage, learnt)
  return bySurah.map(({ total, counts }) => {
    let covered = 0
    for (const at of lemmas) covered += counts[at] ?? 0
    return covered / total
  })
}

/** The progress summary's learnt rows, which every function here takes. */
export const learntOf = (summary) => summary?.filter((row) => row.known) ?? []

/** The credited lemmas spelled out, for marking learnt words in the reader. */
export function learntLemmas(words, coverage, learnt) {
  return new Set([...credited(words, coverage, learnt)].map((at) => coverage.lemmas[at]))
}

/**
 * Which printed words of an ayah are learnt: any piece's lemma will do, as the
 * meter counts it. `ayah` is one entry of the glosses' `lemmas`. Null when none
 * is, so the reader keeps its plain text.
 */
export function learntWords(ayah, lemmas) {
  const marks = ayah?.map((pieces) => pieces.some((lemma) => lemmas.has(lemma)))
  return marks?.some(Boolean) ? marks : null
}

/** The lemmas the learnt rows credit, by the rule above. */
function credited(words, coverage, learnt) {
  const asked = new Map(learnt.map((row) => [row.item, new Set(row.words ?? [])]))
  const weight = (word) => word.lemmas.reduce((sum, at) => sum + coverage.counts[at], 0)
  const picked = []
  const cheapest = new Map()
  for (const word of words) {
    const right = asked.get(word.meaningKey)
    if (!right || !word.lemmas) continue
    if (right.size) {
      if (right.has(word.ar)) picked.push(word)
      continue
    }
    const best = cheapest.get(word.meaningKey)
    if (!best || weight(word) < weight(best)) cheapest.set(word.meaningKey, word)
  }
  return new Set([...picked, ...cheapest.values()].flatMap((word) => word.lemmas))
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
