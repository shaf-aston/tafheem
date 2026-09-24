import { colorFor } from '../theme'

/**
 * The colour a grammatical role is drawn in. What the role means is in
 * lib/grammarTerms.js, keyed by the same names.
 *
 * The backend names the role, `role_key` on every analysed word, and this
 * file turns that name into a token the theme already holds. Nothing here reads
 * the Arabic prose beside it. That text is written for the reader ("فاعل
 * (مرفوع)", "مرفوع لأنه خبر إن"), its wording follows whichever rule fired, and
 * a colour picked by searching it for words is a colour that goes wrong in
 * silence, which is exactly what used to happen: the grid searched Arabic text
 * for the English word 'fail', never matched, and drew every noun and verb the
 * rule engine identified in the default grey.
 *
 * The tarkeeb diagram has always worked the right way round, `--role-<tone>`,
 * named by the backend, coloured by the theme. This is the same seam for the
 * word grid, so the two panels can never disagree about what green means.
 *
 * A word whose role the backend could not settle carries no key and stays grey.
 * No colour is the honest answer there; a plausible one is not.
 */

/** The theme token for a role, or the neutral one when there is no role. */
export const roleVar = (key) => `var(--role-${key || 'default'})`

/** The colour for a corpus part-of-speech code on the Quran tab. */
export const posColor = (tag) => colorFor('pos', tag)
