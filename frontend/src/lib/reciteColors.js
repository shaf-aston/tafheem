/**
 * What each state of a recited word looks like, and what it is called.
 *
 * One place, because the word on the page and the pill on the strip must never
 * disagree about what orange means. The colours are the app's own tokens, so
 * this names states and never picks a colour of its own.
 */
import { CHECK, MISSED, SAID, WRONG } from './follow'

export const LOOK = {
  [SAID]: { colour: 'var(--text-dim)', label: 'right' },
  // Orange is doubt, not a verdict: two different words that sound the same.
  [CHECK]: { colour: 'var(--warn)', label: 'not sure' },
  [WRONG]: { colour: 'var(--danger)', label: 'wrong' },
  [MISSED]: { colour: 'var(--danger)', label: 'not said' },
}

/**
 * A word uncovered by asking for it rather than by saying it.
 *
 * Not one of follow.js's states, and deliberately not: follow marks what was
 * recited, and nobody recited this. It is kept here anyway so that the one file
 * naming what a colour means still names all of them. Faint and dashed, because
 * a word you were given is neither right nor wrong, it is just not yours yet.
 */
export const SHOWN = { colour: 'var(--text-faint)', label: 'shown, not remembered' }

/** How a whole ayah went, as one state: its worst word decides. */
export const verdictOf = (states) => {
  if (states.some((state) => state === WRONG || state === MISSED)) return WRONG
  if (states.some((state) => state === CHECK)) return CHECK
  if (states.length && states.every((state) => state === SAID)) return SAID
  return null
}
