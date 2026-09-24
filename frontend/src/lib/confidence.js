/**
 * How sure the app is allowed to sound, and the words it says it in.
 *
 * Three places show a confidence: the badge beside an answer, the line at the
 * foot of a tab, and the full source list in Settings. They must say the same
 * thing about the same level, a source called "worked out by a fixed rule" in
 * one place and "checked by a person" in another is worse than saying nothing,
 * so the wording lives here and nothing else defines it.
 *
 * The backend sends the level name; data/sources.json is where a source is
 * assigned one. Nothing here decides what any source is.
 */

// "translated" sits between derived and guessed on purpose: the content is the
// book's, only the English wording is a machine's, and the Arabic it came from
// is on the same page to check against. Calling that a guess overstates it.
// Three words is the whole label: it sits beside a passage the reader is
// already reading, and a sentence explaining itself was longer than the thing
// it labelled. What was made, and by what, is all it has to say.
export const CONFIDENCE = {
  verified: { color: 'var(--success)', say: 'Checked by a person' },
  derived: { color: 'var(--primary)', say: 'Worked out by a fixed rule' },
  translated: { color: 'var(--primary)', say: 'AI translated' },
  guessed: { color: 'var(--warn)', say: 'A guess, can be wrong' },
}

/** The level a source claims, or the weakest one if it claims something unknown. */
export const levelOf = (source) => CONFIDENCE[source?.confidence] ?? CONFIDENCE.guessed
