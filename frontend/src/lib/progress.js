/**
 * The only way any panel talks to the progress store.
 *
 * One module holds the addresses, the shape of a saved answer, and what happens
 * when the backend is not there, so a panel learns two functions and no URLs.
 * Nothing about the quiz is in here: an item is whatever stable id the calling
 * panel names its questions by, which is what lets a second panel use this
 * without changing it.
 *
 * Saving is deliberately one-way. An answer is worth keeping but never worth
 * making somebody wait for, and a quiz that stalls or breaks because a database
 * is down is a worse failure than a lost row. So `recordAttempt` never throws,
 * never blocks the next question, and reports whether it landed rather than
 * swallowing the news: a whole session saved to nowhere has to be sayable on
 * screen, or the mistakes list is mysteriously empty a week later.
 */
const BASE = '/api/progress'

/**
 * File one answer. Resolves `{ saved }`; never rejects.
 *
 * `ms` is how long the answer took. Send it as measured, however long: which
 * timings are honest enough to average is the store's rule, not the page's.
 */
export async function recordAttempt({ module, item, correct, ms, context }) {
  try {
    const response = await fetch(`${BASE}/attempts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ module, item, correct, ms, context }),
    })
    return { saved: response.ok }
  } catch {
    return { saved: false } // offline, or no backend: the round carries on
  }
}

/**
 * Delete every saved answer, so Mistakes empties too. Never rejects: the wipe
 * that calls it goes on to clear the browser and reload whether or not the
 * backend was there to hear.
 */
export async function forgetProgress() {
  try {
    const response = await fetch(BASE, { method: 'DELETE' })
    return { deleted: response.ok }
  } catch {
    return { deleted: false }
  }
}

/** Every item answered in this module, with its record. Throws, for react-query. */
export async function fetchSummary(module) {
  const response = await fetch(`${BASE}/summary?module=${encodeURIComponent(module)}`)
  if (!response.ok) throw new Error(`Could not read progress (${response.status})`)
  return (await response.json()).items
}

/** Just the items still waiting to be got right. Throws, for react-query. */
export async function fetchReviewItems(module) {
  const response = await fetch(`${BASE}/review?module=${encodeURIComponent(module)}`)
  if (!response.ok) throw new Error(`Could not read the mistakes list (${response.status})`)
  return (await response.json()).items
}

/** Report something that looks wrong. Resolves `{ saved }`; never rejects. */
export async function leaveFeedback({ module, item, message }) {
  try {
    const response = await fetch(`${BASE}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ module, item, message }),
    })
    return { saved: response.ok }
  } catch {
    return { saved: false }
  }
}
