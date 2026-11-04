/** The ear's per-word sureness, keyed by page place: build, filter, merge. Pure. */
import config from '../../config/recite.json'

/**
 * A word's score: { sure, weak, weakFrom, at, take, sounds }. `sure` is how likely the
 * ear found the word, `weak` the text of its least likely piece and `weakFrom`
 * the characters of the word before it, `at` the second of the recording the
 * word sits at, `take` which recording that is. `detail` is the server's own
 * {weak, weak_from, at} for the word, when it gave one.
 */
const scoreOf = (sure, detail, take = null) => (
  { sure, weak: detail?.weak, weakFrom: detail?.weak_from, at: detail?.at, take, sounds: detail?.sounds }
)

/**
 * One reading's per-ayah answer as scores, keyed by page place; words it did not
 * reach are left out. `detail` is the answer's per-ayah detail, `take` the
 * recording it was scored from.
 */
export const byPlace = (answer = {}, ayahs, detail = {}, take = null) => {
  const out = {}
  for (const { key, spoken } of ayahs) {
    // A count that differs is an ayah the two spellings split into different
    // words; its words cannot be told apart, so it keeps the page's marks.
    const sures = answer[key]
    if (sures?.length !== spoken.length) continue
    sures.forEach((sure, k) => {
      if (sure != null) out[spoken[k]] = scoreOf(sure, detail[key]?.[k], take)
    })
  }
  return out
}

/**
 * A recording's scores, less the low ones it has no right to give: a low score
 * accuses only a word in [from, to), the page words it heard right and settled.
 * Outside them the sound was cut mid-word or never held the word (check() scores
 * the whole ayah), so low there means "not in this recording", and it showed
 * the next words red until a later check, two seconds on, cleared them.
 */
export const settledScores = (scores, from, to) => Object.fromEntries(
  Object.entries(scores).filter(([at, { sure }]) => sure >= config['sure-at'] || (Number(at) >= from && Number(at) < to)),
)

/** The surer of two recordings' scores for each page place, each with its own detail. */
export const surer = (a, b) => {
  const out = { ...a }
  for (const [at, score] of Object.entries(b)) if (!out[at] || out[at].sure < score.sure) out[at] = score
  return out
}
