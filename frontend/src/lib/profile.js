/**
 * Who is learning: a typed name, kept in this browser and sent with every
 * progress call. No password, so anyone typing the same name reads the same
 * record. The server cleans the name again and its spelling wins; this copy
 * exists so the box can say what is wrong before anything is sent.
 */
import CONFIG from '../profile.json'
import { forgetKey, readRaw, writeRaw } from './stored'

export const PROFILE = CONFIG

// Zero-width joiners stay: Persian and Urdu names need them.
const ALLOWED = /^(?:[\p{L}\p{M}\p{Nd} ._-]|\u200c|\u200d)+$/u
const SOMETHING = /[\p{L}\p{Nd}]/u

/** `{ name }` in its one spelling, or `{ error }` saying what to change. */
export function cleanName(raw) {
  // ß folds to ss as the server's casefold does, so both count the same length.
  const name = raw.replace(/\s+/g, ' ').trim().normalize('NFC').toLowerCase().replace(/ß/g, 'ss')
  if (!name) return { error: 'Type a name' }
  if ([...name].length > CONFIG.max) return { error: `Names are at most ${CONFIG.max} characters` }
  if (!ALLOWED.test(name) || !SOMETHING.test(name)) return { error: 'Names use letters, numbers, spaces, - _ .' }
  if (CONFIG.reserved.includes(name)) return { error: 'That name is taken by the app, pick another' }
  return { name }
}

/** The saved name, or '' when nobody has typed one on this device. */
export const getProfile = () => readRaw(CONFIG.storageKey)

export function setProfile(name) {
  if (name) writeRaw(CONFIG.storageKey, name)
  else forgetKey(CONFIG.storageKey)
}

/** The header that says whose record a call is about; empty for the unnamed record. */
export function profileHeaders(name = getProfile()) {
  return name ? { [CONFIG.header]: encodeURIComponent(name) } : {}
}

/** Whether a react-query key reads progress, so a name change refetches it. */
export const readsProgress = (query) => CONFIG.refetch.includes(query.queryKey[0])
