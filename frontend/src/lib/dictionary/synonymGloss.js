/**
 * The short gloss printed beside a synonym.
 *
 * Wiktionary glosses a verbal noun as "verbal noun of عَرَفَ (arafa) (form I)".
 * Beside a synonym that sentence is noise: the word is already there, the verb
 * it comes from is the reader's next click, and only the form says anything
 * new. So the form is kept and the rest dropped. Any other gloss is returned
 * as it came; a "verbal noun of" with no form stated keeps its whole sentence
 * rather than becoming an empty label.
 */
const VERBAL_NOUN = /^verbal noun of .*\((form [^)]+)\)\s*$/

export function synonymGloss(meaning) {
  const form = String(meaning || '').match(VERBAL_NOUN)
  return form ? form[1] : meaning
}
