/**
 * One account's shelf (lib/stored.js) kept the same on every device.
 *
 * The server holds the shelf whole (GET/PUT /api/progress/saved). The rule is
 * the plain one: pull when the page starts or someone logs in, push a moment
 * after any change. The last device to change something wins, which is enough
 * for one person moving between a phone and a laptop. The guest has no shelf
 * on the server: the guest record is shared, so it stays on its device.
 */
import { api } from '../api'
import CONFIG from '../profile.json'
import { getProfile, profileHeaders } from './profile'
import { fillShelf, onChange, shelfOf } from './stored'

const URL = '/progress/saved'
const headers = (name) => ({ headers: profileHeaders(name) })

/** Send this account's whole shelf now. Resolves whether it landed; never rejects. */
export const pushShelf = (name = getProfile()) =>
  api.put(URL, { data: shelfOf(name) }, headers(name)).then(() => true, () => false)

/**
 * Bring the server's shelf onto this device. The server's copy wins; a new
 * account has none yet, so this device's goes up instead. Never rejects:
 * offline, the page runs on what this device has.
 */
export async function pullShelf(name = getProfile()) {
  if (!name) return
  try {
    const { data } = (await api.get(URL, headers(name))).data
    if (Object.keys(data).length) fillShelf(name, data)
    else await pushShelf(name)
  } catch {
    /* offline or refused: this device's copy stands */
  }
}

/** Pull, but give up waiting after pullWaitMs, so a slow server never holds the page. */
export const pullBeforeStart = () =>
  Promise.race([pullShelf(), new Promise((done) => setTimeout(done, CONFIG.pullWaitMs))])

let timer = null
let waiting = null

/** Send the change still waiting out its pushAfterMs, now. */
function sendWaiting() {
  clearTimeout(timer)
  if (waiting) pushShelf(waiting)
  waiting = null
}

/**
 * Push every change to a logged-in shelf, a burst of changes as one. Returns
 * the way to stop. A page being hidden (tab closed, phone locked) sends what is
 * still waiting at once: the next device pulls this copy and the server's wins.
 */
export function keepShelfInStep() {
  const hidden = () => document.visibilityState === 'hidden' && sendWaiting()
  document.addEventListener('visibilitychange', hidden)
  const stop = onChange(() => {
    waiting = getProfile()
    if (!waiting) return
    clearTimeout(timer)
    timer = setTimeout(sendWaiting, CONFIG.pushAfterMs)
  })
  return () => {
    stop()
    document.removeEventListener('visibilitychange', hidden)
  }
}

/** Sign-up that kept the guest's answers keeps the guest's shelf too. */
export function copyGuestShelf(name) {
  fillShelf(name, shelfOf(''))
  return pushShelf(name)
}

/** A deleted account's shelf goes from this device too; the server's went with it. */
export const forgetShelf = (name = getProfile()) => fillShelf(name, {})
