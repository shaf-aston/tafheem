/**
 * Who is learning: a typed name, kept in this browser and sent with every
 * progress call. No password, so anyone typing the same name reads the same
 * record. The rules for a name live on the server only; this keeps whatever
 * spelling the server handed back (lib/progress.js startProfile).
 */
import CONFIG from '../profile.json'
import { readRaw, writeRaw } from './stored'

/** The saved name, or '' when nobody has typed one on this device. */
export const getProfile = () => readRaw(CONFIG.storageKey)

export const setProfile = (name) => writeRaw(CONFIG.storageKey, name)

/** The header that says whose record a call is about; empty for the unnamed record. */
export function profileHeaders(name = getProfile()) {
  return name ? { [CONFIG.header]: encodeURIComponent(name) } : {}
}

/** Whether a react-query key reads progress, so a name change refetches it. */
export const readsProgress = (query) => CONFIG.refetch.includes(query.queryKey[0])
