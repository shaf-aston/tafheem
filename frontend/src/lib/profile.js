/**
 * Who is logged in: a username, kept in this browser and sent with every
 * progress call. No password, which is agreed. The rules for a name live on
 * the server only; this keeps whatever spelling the server handed back
 * (lib/progress.js signUp, logIn).
 */
import CONFIG from '../profile.json'
import { forgetKey, readRaw, writeRaw } from './stored'

/** The saved name, or '' when nobody has typed one on this device. */
export const getProfile = () => readRaw(CONFIG.storageKey)

export const setProfile = (name) => writeRaw(CONFIG.storageKey, name)

/** Log out: back to the guest record. */
export const logOut = () => forgetKey(CONFIG.storageKey)

/** The header that says whose record a call is about; empty for the unnamed record. */
export function profileHeaders(name = getProfile()) {
  return name ? { [CONFIG.header]: encodeURIComponent(name) } : {}
}

/** Whether a react-query key reads progress, so a name change refetches it. */
export const readsProgress = (query) => CONFIG.refetch.includes(query.queryKey[0])
