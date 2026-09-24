/**
 * Which root the classical panel should ask about.
 *
 * The dictionary is searched by word *or* by root, so what was typed is not
 * always a root. Guessing, quietly taking the root off the first result, would
 * answer a question the reader never asked, and they would have no way to tell.
 * So the typed text is always what is asked about, and any different roots the
 * results carry are offered as something to tap, never applied on their own.
 *
 * Nothing here folds letters. The backend normalises with the very function that
 * built its index, so the raw text is sent and the backend reports back the exact
 * letters it searched. Mirroring that folding here is how the two would drift.
 * bareForm is used only to decide whether two roots are worth showing twice.
 */
import { bareForm } from './arabicText'

// More than a few chips stops being a choice and starts being a list.
const MAX_ALTERNATES = 3

// A root is written "كتب" in one list and "ك-ت-ب" in another. For deciding
// whether two chips ask the same question, only the Arabic letters count.
//
// Written as "keep the letters" rather than "drop these separators" on purpose:
// the list of things that separate letters is open, hyphen, dash, space,
// non-breaking space, zero-width space; and the invisible ones cannot be seen
// in a diff, so a list of them is a list that quietly goes out of date.
//
// Folded only to compare two chips. What is shown, and what is sent to the
// backend, is always exactly what the entry said.
const sameRoot = (text) => bareForm(text).replace(/\P{Script=Arabic}/gu, '')

export function pickRoots(query, results = []) {
  const primary = (query ?? '').trim()
  const seen = new Set([sameRoot(primary)])
  const alternates = []

  for (const entry of results) {
    const root = (entry?.root ?? '').trim()
    const key = sameRoot(root)
    if (!root || seen.has(key)) continue
    seen.add(key)
    alternates.push(root)
    if (alternates.length === MAX_ALTERNATES) break
  }

  return { primary, alternates }
}
