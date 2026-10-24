/**
 * Who is logged in: a username, kept in this browser and sent with every
 * progress call. No password, which is agreed. The rules for a name live on
 * the server only; this keeps whatever spelling the server handed back
 * (lib/learner/progress.js signUp, logIn).
 *
 * Nobody logged in is this device's own guest record, named by a random id made once (`deviceId`), so two
 * guests on two devices never see each other's answers; sign-up with "keep" moves this device's onto the name.
 *
 * Switching person reloads the page: every setting and remembered choice is
 * filed under the name (lib/store/stored.js), and a reload is the one way every panel
 * reads the new person's at once.
 */
import CONFIG from '../../config/profile.json'
import { forgetDevice, readDevice, writeDevice } from '../store/stored'

/** The saved name, or '' when nobody has typed one on this device. */
export const getProfile = () => readDevice(CONFIG.storageKey)

const reload = () => globalThis.location.reload()

/** Become `name`, the server's spelling of it. */
export const logInAs = (name) => { writeDevice(CONFIG.storageKey, name); reload() }

/** Back to this device's guest record. The shelf stays filed under the name for next time. */
export const logOut = () => { forgetDevice(CONFIG.storageKey); reload() }

// 128 random bits as 32 lowercase hex: the only id the server takes (services/learner/username.py device_key).
const ID = /^[0-9a-f]{32}$/
// getRandomValues, not randomUUID: the second exists only on https or localhost, and the app is tried over LAN http.
const fresh = () => Array.from(globalThis.crypto.getRandomValues(new Uint8Array(16)), (byte) => byte.toString(16).padStart(2, '0')).join('')
// The id for this visit when the browser will not keep one (private browsing, storage blocked).
let held = ''

/** This device's guest id: the kept one, else a new one, kept. */
export function deviceId() {
  const kept = readDevice(CONFIG.deviceKey)
  if (ID.test(kept)) return kept
  if (!ID.test(held)) held = fresh()
  writeDevice(CONFIG.deviceKey, held)
  return held
}

/** The header that says whose record a call is about: the name, or this device's guest id when there is none. */
export function profileHeaders(name = getProfile()) {
  return name ? { [CONFIG.header]: encodeURIComponent(name) } : { [CONFIG.guestHeader]: deviceId() }
}
