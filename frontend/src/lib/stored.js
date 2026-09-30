/**
 * The one way to forget everything this app keeps in the browser: settings,
 * remembered choices (useRemembered), recent searches (useHistory), best streak,
 * the walked path (session.js).
 *
 * Clears the whole store rather than a written list of key names, which would
 * go stale the first time a panel remembers something new and then clear less
 * than the button says. The store holds this app's things only.
 *
 * Quiz answers are rows in a database on the machine, not in the browser, so
 * they go through lib/progress.js first; "clear it all" has to mean Mistakes
 * as well, or the button says more than it does.
 */
import { forgetProgress } from './progress'

// Every browser-store read and write in lib/ goes through these. Storage can
// throw (private browsing, quota), so none of them ever does.

/** The stored string as written, or the fallback when missing or storage throws. */
export function readRaw(key, fallback = '') {
  try {
    return globalThis.localStorage?.getItem(key) ?? fallback
  } catch {
    return fallback
  }
}

/** Store a string as is; in private browsing it is silently kept for this visit only. */
export function writeRaw(key, text) {
  try {
    globalThis.localStorage?.setItem(key, text)
  } catch {
    /* private browsing, the value still holds for this visit */
  }
}

/** The stored JSON value, or the fallback when missing, unparseable or storage throws. */
export function readSaved(key, fallback) {
  try {
    const text = globalThis.localStorage?.getItem(key)
    return text == null ? fallback : JSON.parse(text)
  } catch {
    return fallback
  }
}

/** Store a value as JSON, same private-browsing rule as writeRaw. */
export function writeSaved(key, value) {
  writeRaw(key, JSON.stringify(value))
}

/** Forget one key. */
export function forgetKey(key) {
  try {
    globalThis.localStorage?.removeItem(key)
  } catch {
    /* nothing stored to remove */
  }
}

/**
 * Forget it all, then reload.
 *
 * The reload is required, not tidiness: settings and remembered choices are
 * also held in React state, so clearing underneath them leaves stale values on
 * screen and the next click writes one straight back.
 */
export async function forgetSaved() {
  await forgetProgress()
  try {
    globalThis.localStorage?.clear()
  } catch {
    /* private browsing: nothing was kept */
  }
  globalThis.location?.reload()
}
