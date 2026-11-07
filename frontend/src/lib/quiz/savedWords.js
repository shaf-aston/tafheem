/**
 * Words saved from the Qur'an reader for Review (components/grammar/SaveWord.jsx).
 *
 * Kept on the learner's shelf under progressKey, so an account carries them to
 * any device and Start over forgets them with the rest of the record. A saved
 * word is saved as a word of the quiz table, found by its lemma, so Review asks
 * it like any other and the store files the answer under its meaningKey. It
 * waits in Review until the store calls it known; from then on the store's own
 * spacing brings it back, as for every word.
 */
import { progressKey, readSaved } from '../store/stored'

export const SAVED_WORDS = progressKey('saved-words')

/** Every saved word, oldest first: `{ key, lemma }`. */
export const readSavedWords = () => readSaved(SAVED_WORDS, [])

/** The surah:ayah a corpus word was seen in ("2:255" of "2:255:3"), or null for a word from elsewhere. */
export const seenAt = (word) => word?.position?.match(/^(\d+:\d+):\d+$/)?.[1] ?? null

/**
 * The table word a Qur'an word is, by its lemma, or null: a particle the lists
 * leave out cannot be asked, so it is never offered for saving. Compared
 * normalised, since a shadda and its vowel are written in either order.
 */
export function tableWordFor(lemma, words, coverage) {
  const wanted = lemma?.normalize()
  const at = wanted ? coverage.lemmas.findIndex((one) => one.normalize() === wanted) : -1
  return at < 0 ? null : words.find((word) => word.lemmas?.includes(at)) ?? null
}

/** The saved entry for a Qur'an word and the table word it is. */
export const savedEntry = (word, match) => ({ key: match.meaningKey, lemma: word.lemma })

/**
 * The saved words Review asks besides what the store says is due: any the
 * store does not call known yet, each once, and none already in `due`.
 */
export function savedToAsk(saved, summary, due) {
  const known = new Set(summary.filter((row) => row.known).map((row) => row.item))
  const owed = new Set(due)
  return [...new Set(saved.map((entry) => entry.key))].filter((key) => !known.has(key) && !owed.has(key))
}
