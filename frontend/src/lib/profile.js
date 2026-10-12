/**
 * Who is logged in: a username, kept in this browser and sent with every
 * progress call. No password, which is agreed. The rules for a name live on
 * the server only; this keeps whatever spelling the server handed back
 * (lib/progress.js signUp, logIn).
 *
 * Switching person reloads the page: every setting and remembered choice is
 * filed under the name (lib/stored.js), and a reload is the one way every panel
 * reads the new person's at once.
 */
import CONFIG from '../profile.json'
import { forgetDevice, readDevice, writeDevice } from './stored'

/** The saved name, or '' when nobody has typed one on this device. */
export const getProfile = () => readDevice(CONFIG.storageKey)

const reload = () => globalThis.location.reload()

/** Become `name`, the server's spelling of it. */
export const logInAs = (name) => { writeDevice(CONFIG.storageKey, name); reload() }

/** Back to the guest record. The shelf stays filed under the name for next time. */
export const logOut = () => { forgetDevice(CONFIG.storageKey); reload() }

/** The header that says whose record a call is about; empty for the unnamed record. */
export function profileHeaders(name = getProfile()) {
  return name ? { [CONFIG.header]: encodeURIComponent(name) } : {}
}
