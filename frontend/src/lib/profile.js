/**
 * Who is signed in: a username and the key its sign-in handed back, kept in
 * this browser and sent with every progress call. The rules for a name live on
 * the server only; this keeps whatever spelling the server handed back
 * (lib/progress.js signUp, signIn).
 */
import CONFIG from '../profile.json'
import { forgetDevice, readDevice, writeDevice } from './stored'

/** The saved name, or '' when nobody has typed one on this device. */
export const getProfile = () => readDevice(CONFIG.storageKey)

export function setProfile(name, key) {
  writeDevice(CONFIG.storageKey, name)
  writeDevice(CONFIG.keyStorageKey, key)
}

/** Log out: back to the guest record. The shelf stays filed under the name for next time. */
export function logOut() {
  forgetDevice(CONFIG.storageKey)
  forgetDevice(CONFIG.keyStorageKey)
}

/** The headers that say whose record a call is about; empty for the unnamed record.
 *  The key goes only with the signed-in name, never with one being tried. */
export function profileHeaders(name = getProfile()) {
  if (!name) return {}
  const key = name === getProfile() && readDevice(CONFIG.keyStorageKey)
  return { [CONFIG.header]: encodeURIComponent(name), ...(key && { [CONFIG.keyHeader]: key }) }
}
