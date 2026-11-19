/**
 * Answers given with no signal, kept on this device until the server can take them.
 *
 * A lesson on a train is still a lesson: its answers are worth the XP and the Review
 * they would have earned online. So an answer that never reached a server able to judge
 * it (no signal, the server down or too busy) waits here, filed with the header that
 * says whose it is, and is sent, oldest first, when the signal is back. An answer the
 * server did judge and refuse is never kept: sending it again would only be refused again.
 * Sending is lib/learner/progress.js's; this module only keeps the list.
 */
import PROFILE from '../../config/profile.json'
import { forgetDevice, readDevice, writeDevice } from '../store/device'

const { key: KEY, max: MAX } = PROFILE.outbox

/** `[{ body, headers }]`, oldest first; an unreadable list is an empty one. */
export function waiting() {
  try {
    const list = JSON.parse(readDevice(KEY, '[]'))
    return Array.isArray(list) ? list : []
  } catch {
    return []
  }
}

const keep = (list) => (list.length ? writeDevice(KEY, JSON.stringify(list.slice(-MAX))) : forgetDevice(KEY))

/** Keep one answer for later, under whoever gave it. */
export const hold = (body, headers) => keep([...waiting(), { body, headers }])

/** Drop every waiting answer: Start over means these too. */
export const forgetWaiting = () => forgetDevice(KEY)

/** No answer from a server that could judge it: worth sending again later. */
export function worthRetrying(error) {
  const status = error?.response?.status
  return !status || status >= 500 || status === 429
}

let sending = null

/**
 * Send what waits through `post(body, headers)`, oldest first, one at a time. Stops at the
 * first that still cannot land, and drops one the server refuses. Resolves how many landed.
 * One run at a time: a second call while one runs gets the same run.
 */
export function sendWaiting(post) {
  sending ??= (async () => {
    let landed = 0
    for (let first = waiting()[0]; first; first = waiting()[0]) {
      try {
        await post(first.body, first.headers)
        landed += 1
      } catch (error) {
        if (worthRetrying(error)) break
      }
      keep(waiting().slice(1))
    }
    return landed
  })().finally(() => { sending = null })
  return sending
}
