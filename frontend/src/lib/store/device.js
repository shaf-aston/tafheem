/**
 * This browser's own storage, below anyone's shelf: the keys that belong to the
 * device, not to whoever uses it, and the three calls that touch them. Nothing
 * here knows about accounts or records (lib/store/stored.js files those on top),
 * so a page that only needs a device key, the landing page handing its look to
 * the app, reads it without the learner's code coming along.
 */
import PROFILE from '../../config/profile.json'
import THEME from '../../config/theme.json'

/** Keys that belong to this browser, not to whoever uses it: never a shelf, never wiped by Start over. */
export const DEVICE_KEYS = Object.freeze({
  profile: PROFILE.storageKey,
  guest: PROFILE.deviceKey,
  recorder: 'recorder-key',
  installDismissed: 'install-dismissed',
  themeHint: THEME.themes['hint-key'],
})

/** The store itself, or null where there is none or it throws on touch. */
export function store() {
  try {
    return globalThis.localStorage ?? null
  } catch {
    return null
  }
}

/** A key as the device holds it: the bare key, before any name is put on it. */
export function readDevice(key, fallback = '') {
  try {
    return store()?.getItem(key) ?? fallback
  } catch {
    return fallback
  }
}

export function writeDevice(key, text) {
  try {
    store()?.setItem(key, text)
  } catch {
    /* private browsing, the value still holds for this visit */
  }
}

export function forgetDevice(key) {
  try {
    store()?.removeItem(key)
  } catch {
    /* nothing stored to remove */
  }
}
