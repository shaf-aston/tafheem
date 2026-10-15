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
const headers = (name) => ({ headers: profileHeaders(name) })

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
 * Start using a typed name. Resolves `{ name, moved }`: the server's spelling,
 * which is what to keep, and how many unnamed answers `keep` moved onto it.
 * Throws, so the box can say why a name was refused.
 */
export const startProfile = (typed, keep) =>
  api.post(`${BASE}/profile`, { keep }, headers(typed)).then((r) => r.data)

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

/**
 * Forget it all, then reload: the answers on the server, then the whole browser
 * store (stored.js).
 *
 * Clears the whole store rather than a written list of key names, which would
 * go stale the first time a panel remembers something new and then clear less
 * than the button says. The store holds this app's things only. Quiz answers
 * are rows in a database on the machine, not in the browser, so they go first;
 * "clear it all" has to mean Review as well, or the button says more than it does.
 *
 * The reload is required, not tidiness: settings and remembered choices are
 * also held in React state, so clearing underneath them leaves stale values on
 * screen and the next click writes one straight back.
 */
export async function forgetSaved() {
  await forgetProgress()
  try {
    globalThis.localStorage?.clear()
  } catch {
    /* private browsing: nothing was kept */
  }
  globalThis.location?.reload()
}
