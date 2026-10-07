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
 * screen, or the review list is mysteriously empty a week later.
 */
import { api } from '../api'
import { profileHeaders } from './profile'

const BASE = '/progress'

// Every call says whose record it is about (lib/profile.js), read at call time
// so a name switched a moment ago is the one sent.
const headers = () => ({ headers: profileHeaders() })

/** Resolves whether the server took it; never rejects (offline or refused is false). */
const landed = (request) => request.then(() => true, () => false)

/**
 * File one answer. Resolves `{ saved }`; never rejects.
 *
 * `ms` is how long the answer took. Send it as measured, however long: which
 * timings are honest enough to average is the store's rule, not the page's.
 */
export async function recordAttempt({ module, item, correct, ms, context }) {
  return { saved: await landed(api.post(`${BASE}/attempts`, { module, item, correct, ms, context }, headers())) }
}

/**
 * Delete every saved answer, so Review empties too. Never rejects: the wipe
 * that calls it goes on to clear the browser and reload whether or not the
 * backend was there to hear.
 */
export async function forgetProgress() {
  return { deleted: await landed(api.delete(BASE, headers())) }
}

/**
 * Move the answers given before names existed onto the name now saved.
 * Resolves the number moved, or null when it did not land; never rejects.
 */
export const claimProgress = () =>
  api.post(`${BASE}/claim`, {}, headers()).then((r) => r.data.moved, () => null)

/** Every item answered in this module, with its record. Throws, for react-query. */
export const fetchSummary = (module) =>
  api.get(`${BASE}/summary`, { params: { module }, ...headers() }).then((r) => r.data.items)

/** Just the items due for review now, longest-waiting first. Throws, for react-query. */
export const fetchReviewItems = (module) =>
  api.get(`${BASE}/review`, { params: { module }, ...headers() }).then((r) => r.data.items)

/** Report something that looks wrong. Resolves `{ saved }`; never rejects. */
export async function leaveFeedback({ module, item, message }) {
  return { saved: await landed(api.post(`${BASE}/feedback`, { module, item, message }, headers())) }
}
