/**
 * Grow's screens as addresses: /app/grow (home), /app/grow/hadith (a world), /app/grow/hadith/lesson (a lesson there).
 * Pure. `placeOf` reads the tab's value (lib/tabUrl.js writes it), `valueOf` writes one; GrowPanel is the caller.
 * A lesson's cards are not in the address: arriving at one starts a fresh lesson.
 */

const LESSON = 'lesson'

/** `{ at: 'home' }`, `{ at: 'world', id }` or `{ at: 'lesson', id }`; anything unknown is home. */
export function placeOf(value, worldIds, lessonIds) {
  const [id, step, ...rest] = (value ?? '').split('/').filter(Boolean)
  if (!id || !worldIds.includes(id) || rest.length) return { at: 'home' }
  if (!step) return { at: 'world', id }
  return step === LESSON && lessonIds.includes(id) ? { at: 'lesson', id } : { at: 'world', id }
}

/** The tab value for a screen: null for home. */
export const valueOf = (view) => {
  if (view.at === 'world') return view.id
  if (view.at === 'lesson') return `${view.id}/${LESSON}`
  return null
}
