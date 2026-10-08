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
 * Take a free username, or log in to one already taken. Both resolve
 * `{ name, moved }`: the server's spelling, which is what to keep, and how many
 * guest answers `keep` moved onto it. Both throw, so the box can say why
 * (taken, no such username, not a name).
 */
export const signUp = (typed, keep) =>
  api.post(`${BASE}/signup`, { keep }, headers(typed)).then((r) => r.data)

export const logIn = (typed) =>
  api.post(`${BASE}/login`, {}, headers(typed)).then((r) => r.data)

/** The profile page: `{ name, joined, answers }`. Throws, for react-query. */
export const fetchAccount = () => api.get(`${BASE}/account`, headers()).then((r) => r.data)

/** Delete this username and its answers. Throws, so the button can say it failed. */
export const deleteAccount = () => api.delete(`${BASE}/account`, headers()).then((r) => r.data)

/** `{ rows, you }`: accounts by words learnt, and this one's place. Throws, for react-query. */
export const fetchLeaderboard = (module) =>
  api.get(`${BASE}/leaderboard`, { params: { module }, ...headers() }).then((r) => r.data)

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

/** Every username, for the log-in box while in beta. Throws (404 once beta is over), for react-query. */
export const fetchAccountNames = () => api.get(`${BASE}/accounts`).then((r) => r.data.names)

/** `{ tree, teams }`: everyone under this account with their progress, and the teams it is in. */
export const fetchTeam = (module) =>
  api.get(`${BASE}/team`, { params: { module }, ...headers() }).then((r) => r.data)

/** Put a username in this account's team. Resolves the new team; throws, so the box can say why. */
export const addMember = (member, module) =>
  api.post(`${BASE}/team`, { member }, { params: { module }, ...headers() }).then((r) => r.data)

/** Part a member from a team; the team or the member may. Resolves the new team. */
export const removeMember = (team, member, module) =>
  api.delete(`${BASE}/team`, { params: { team, member, module }, ...headers() }).then((r) => r.data)
