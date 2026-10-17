/**
 * Grow's screens as addresses: /app/grow (home), /app/grow/hadith (a world), /app/grow/hadith/lesson (a lesson there).
 * A book world goes deeper: /app/grow/fiqh/tahara (a part), /app/grow/fiqh/tahara/wudu (a lesson), /app/grow/fiqh/review.
 * Pure. `placeOf` reads the tab's value (lib/tabUrl.js writes it), `valueOf` writes one; GrowPanel is the caller.
 * A lesson's cards are not in the address: arriving at one starts a fresh lesson.
 */

const LESSON = 'lesson'
const REVIEW = 'review'

/** A book world's address after its id: a part, a lesson in a part, or the review. Which parts exist is the screen's to check. */
function bookPlace(id, [part, lesson, ...rest]) {
  if (!part || rest.length) return { at: 'world', id }
  if (part === REVIEW) return lesson ? { at: 'world', id } : { at: 'lesson', id, lesson: REVIEW }
  return lesson ? { at: 'lesson', id, part, lesson } : { at: 'world', id, part }
}

/** `{ at: 'home' }`, `{ at: 'world', id, part? }` or `{ at: 'lesson', id, part?, lesson? }`; anything unknown is home. */
export function placeOf(value, worldIds, lessonIds, bookIds = []) {
  const [id, ...steps] = (value ?? '').split('/').filter(Boolean)
  if (!id || !worldIds.includes(id)) return { at: 'home' }
  if (bookIds.includes(id)) return bookPlace(id, steps)
  const [step, ...rest] = steps
  if (rest.length) return { at: 'home' }
  if (!step) return { at: 'world', id }
  return step === LESSON && lessonIds.includes(id) ? { at: 'lesson', id } : { at: 'world', id }
}

/** The tab value for a screen: null for home. */
export const valueOf = (view) => {
  if (view.at === 'world') return view.part ? `${view.id}/${view.part}` : view.id
  if (view.at === 'lesson') {
    if (view.lesson === REVIEW) return `${view.id}/${REVIEW}`
    return view.lesson ? `${view.id}/${view.part}/${view.lesson}` : `${view.id}/${LESSON}`
  }
  return null
}
