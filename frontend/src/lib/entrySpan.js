/**
 * How many grid columns a small dictionary card takes: one, or two.
 *
 * The words beside the searched one differ a lot in weight. استعلم has one
 * sense, علم has eight and a band of synonyms. Equal cards made the light ones
 * mostly empty and the heavy ones a scroll, so a card is sized by what is in
 * it. The thresholds are in dictionary.json; this is its only reader.
 */
import config from '../dictionary.json'

const TIERS = config.forms.tiers

/** @returns {1 | 2 | 3} */
export function entrySpan(entry) {
  const definitions = entry.definitions ?? []
  const letters = definitions.reduce((n, d) => n + d.length, 0)
  const synonyms = (entry.synonyms ?? []).some((list) => list.length > 0)

  const hit = TIERS.find((t) => definitions.length >= t.senses
    || letters >= t.letters
    || (t.synonyms && synonyms))
  return hit?.cols ?? 1
}
