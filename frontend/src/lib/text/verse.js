/**
 * A bayt's two halves. OpenITI marks a line of verse with " % " between its hemistichs (the Jawhara's bayts come
 * so); that mark is the file's, not the poem's, so it is split on here and never printed. One place, used by
 * ui/ArabicText and ChooseCard, so every card, recap and shelf of a verse book reads the same.
 */
const MARK = /\s%\s/

/** The halves of a line of verse, trimmed; a single-item list for text that is not verse. */
export const hemistichs = (ar) => (typeof ar === 'string' ? ar.split(MARK).map((half) => half.trim()) : [ar])

export const isVerse = (ar) => typeof ar === 'string' && MARK.test(ar)
