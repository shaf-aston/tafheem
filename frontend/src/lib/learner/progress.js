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
import { api } from '../../api'
import { logOut, profileHeaders } from './profile'
import { announce, tz } from './rewards'

const BASE = '/progress'

// Every call says whose record it is about: api/client.js adds the logged-in name to
// every request. Sign-up and log-in send the name typed instead.
const headers = (name) => ({ headers: profileHeaders(name) })

/** Resolves whether the server took it; never rejects (offline or refused is false). */
const landed = (request) => request.then(() => true, () => false)

/**
 * File one answer. Resolves `{ saved, earned }` (earned XP); never rejects.
 *
 * `ms` is how long the answer took. Send it as measured, however long: which
 * timings are honest enough to average is the store's rule, not the page's.
 */
export async function recordAttempt({ module, item, correct, ms, context }) {
  let response
  try {
    response = await api.post(`${BASE}/attempts`, { module, item, correct, ms, context, tz: tz() })
  } catch {
    return { saved: false }
  }
  // Tell the XP display (lib/learner/rewards.js).
  announce(response.data)
  return { saved: true, earned: response.data?.earned ?? 0 }
}

/**
 * Delete every saved answer, so Review empties too. Never rejects: the wipe
 * that calls it goes on to clear the browser and reload whether or not the
 * backend was there to hear.
 */
export async function forgetProgress() {
  return { deleted: await landed(api.delete(BASE)) }
}

/**
 * Take a free username (`keep` moves the guest's answers onto it), or log in to
 * one already taken. Both resolve the account, whose `name` is the server's
 * spelling, the one to keep, and `recovery`: the account's new recovery code
 * when one was made, to show once (the server keeps only its seal). The proof
 * that this browser is the account's is an HttpOnly cookie the page never sees
 * (backend/identity.py).
 *
 * Log-in sends the recovery code when one is typed. Without one it works on a
 * browser already holding the account's cookie, or, for an account from before
 * codes, by claiming it; anything else is a 403 asking for the code
 * (`needsCode`). Both throw, so the box can say why (taken, no such username,
 * wrong code, not a name).
 *
 * Both say `shows_code`: this page shows a new code (pages from before codes
 * never did, so the server makes none for them; this page claims the account
 * on its next load instead, and shows it then).
 */
export const signUp = (typed, keep) =>
  api.post(`${BASE}/signup`, { keep, shows_code: true }, headers(typed)).then((r) => r.data)

export const logIn = (typed, code) =>
  api.post(`${BASE}/login`, { shows_code: true, ...(code && { code }) }, headers(typed)).then((r) => r.data)

/** A refusal that the recovery code would answer: missing or wrong. */
export const needsCode = (error) => error?.response?.status === 403

/**
 * A new recovery code; the old one stops working. Resolves the code, to show once. Throws: a 403
 * (`needsCode`) asks for the current code, which is needed unless this device logged in moments ago.
 * `firstCode` asks only for an account's first (a 409 if another tab made it), so it never replaces one on screen.
 */
export const newRecoveryCode = (current) =>
  api.post(`${BASE}/recovery`, current ? { code: current } : {}).then((r) => r.data.code)

export const firstCode = () => api.post(`${BASE}/recovery`, { first: true }).then((r) => r.data.code)

/** Log out every other device of this account. Resolves how many. Throws. */
export const logOutOthers = () => api.delete(`${BASE}/sessions`).then((r) => r.data.deleted)

/**
 * Log out here: the server forgets this browser's token and drops the cookie,
 * then the page goes back to the guest record. Only then: the cookie is out of
 * the page's reach, and while it stays, anyone typing the name on this browser
 * is let in without the code. So a log-out the server did not hear (offline, an
 * error) throws, and the page stays logged in to say so.
 */
export async function logOutHere() {
  await api.delete(`${BASE}/session`)
  logOut()
}

/** The profile page: `{ name, joined, answers }`. Throws, for react-query. */
export const fetchAccount = () => api.get(`${BASE}/account`).then((r) => r.data)

/** Delete this username and its answers. Throws, so the button can say it failed. */
export const deleteAccount = () => api.delete(`${BASE}/account`).then((r) => r.data)

/** `{ modules, attempts, correct, learnt, streak }`: every module answered in. Throws, for react-query. */
export const fetchOverview = () => api.get(`${BASE}/overview`, { params: { tz: tz() } }).then((r) => r.data)

/** `{ xp, xpToday, level, into, need, streak }`. Throws, for react-query. */
export const fetchRewards = () => api.get(`${BASE}/rewards`, { params: { tz: tz() } }).then((r) => r.data)

/** `{ rows, you }`: a circle's joined members (when `circle` is given) or the public accounts, by words learnt,
 *  and this one's place. Throws, for react-query. */
export const fetchLeaderboard = (module, circle) =>
  api.get(`${BASE}/leaderboard`, { params: { module, circle } }).then((r) => r.data)

/** Show in (true) or hide from the global ranking. Resolves the account; throws. */
export const setPublic = (isPublic) =>
  api.put(`${BASE}/account/public`, { public: isPublic }).then((r) => r.data)

/** Every item answered in this module, with its record. Throws, for react-query. */
export const fetchSummary = (module) =>
  api.get(`${BASE}/summary`, { params: { module } }).then((r) => r.data.items)

/** Just the items due for review now, longest-waiting first. Throws, for react-query. */
export const fetchReviewItems = (module) =>
  api.get(`${BASE}/review`, { params: { module } }).then((r) => r.data.items)

/** Report something that looks wrong. Resolves `{ saved }`; never rejects. */
export async function leaveFeedback({ module, item, message }) {
  return { saved: await landed(api.post(`${BASE}/feedback`, { module, item, message })) }
}

/** Every username, for the log-in box while in beta. Throws (404 once beta is over), for react-query. */
export const fetchAccountNames = () => api.get(`${BASE}/accounts`).then((r) => r.data.names)

// Circles: everything about who may do or see what is the server's (services/learner/progress_store.py);
// these only call it. Each one throws, so the box can say why.
const circlePath = (id) => `${BASE}/circles/${id}`
const memberPath = (id, member) => `${circlePath(id)}/members/${encodeURIComponent(member)}`

/** `{ kinds, circles }`: every circle I am in, invites included (status "invited"), and the kinds a new one may take. */
export const fetchCircles = () => api.get(`${BASE}/circles`).then((r) => r.data)

/** Make a circle, optionally inside one I administer. Resolves it as `fetchCircle` does. */
export const createCircle = (circle) => api.post(`${BASE}/circles`, circle).then((r) => r.data)

/** `{ id, name, kind, parent, role, members, inside }`: the people I may see in it, each with `seeable`. */
export const fetchCircle = (id) => api.get(circlePath(id)).then((r) => r.data)

export const deleteCircle = (id) => api.delete(circlePath(id)).then((r) => r.data)

/** Resolves the circle; the person sees nothing until they accept. */
export const inviteMember = (id, member, role) =>
  api.post(`${circlePath(id)}/members`, { member, role }).then((r) => r.data)

/** Accept (true) or decline (false) an invite. Resolves my circles. */
export const answerInvite = (id, accept) =>
  api.post(`${circlePath(id)}/${accept ? 'accept' : 'decline'}`).then((r) => r.data)

export const leaveCircle = (id) => api.post(`${circlePath(id)}/leave`).then((r) => r.data)

export const removeMember = (id, member) => api.delete(memberPath(id, member)).then((r) => r.data)

export const setRole = (id, member, role) => api.put(memberPath(id, member), { role }).then((r) => r.data)

/** Move a circle inside another I administer (`parent` an id), or out on its own (null). Resolves the circle. */
export const moveCircle = (id, parent) => api.put(`${circlePath(id)}/parent`, { parent }).then((r) => r.data)

/** A member's `fetchOverview`, if the circles' rules let me see it. */
export const fetchMemberOverview = (id, member) =>
  api.get(`${memberPath(id, member)}/overview`).then((r) => r.data)
