import { useState } from 'react'

const NOTHING = { answers: {}, checked: false, shown: new Set() }

/**
 * Names one set of gaps. Every setting that decides which words are missing is
 * in it, so a page with the same name has the same gaps and an answer saved
 * under it still lands on the right word. Nothing that does not move a gap
 * (the meaning shown, the card open) belongs here.
 */
export const gapsScope = ({ bookId, part, pageNumber, way, difficulty, deal, pinned }) =>
  [bookId, part, pageNumber, way, difficulty, deal, pinned].join('/')

const resolve = (next, was) => (typeof next === 'function' ? next(was) : next)

/**
 * What has been answered, whether the page is marked, and the words shown, kept
 * for every set of gaps the reader has been on. Turning a page and coming back
 * finds the page as it was left; only "Try again" (`fresh`) empties one.
 */
export function useAnswers(scope) {
  const [bank, setBank] = useState({})
  const here = bank[scope] ?? NOTHING
  const change = (field) => (next) => setBank((was) => {
    const now = was[scope] ?? NOTHING
    return { ...was, [scope]: { ...now, [field]: resolve(next, now[field]) } }
  })
  // Words uncovered by asking rather than by saying them. Kept apart from the
  // marks for exactly that reason: being shown a word is not reciting it.
  return {
    ...here,
    setAnswers: change('answers'),
    setChecked: change('checked'),
    setShown: change('shown'),
    fresh: () => setBank((was) => ({ ...was, [scope]: NOTHING })),
  }
}
