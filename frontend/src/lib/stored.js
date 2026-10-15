/**
 * The browser store: everything this app keeps in the browser goes through
 * here, settings, remembered choices (useRemembered), recent searches
 * (useHistory), best streak, the walked path (session.js). Forgetting all of it
 * is forgetSaved, in lib/progress.js, since it also forgets the answers kept on
 * the server.
 */

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

/**
 * The learner's own record (Grow steps, Tamreen answers, best streak) is kept
 * under this prefix, so Start over forgets all of it by one rule: a new module's
 * record is covered the day it is named through progressKey, with no list to update.
 */
const PROGRESS = 'progress:'
export const progressKey = (name) => `${PROGRESS}${name}`

/** Forget every record kept under progressKey; choices and settings stay. */
export function forgetProgressKeys() {
  try {
    const store = globalThis.localStorage
    const keys = Array.from({ length: store?.length ?? 0 }, (_, index) => store.key(index))
    keys.filter((key) => key?.startsWith(PROGRESS)).forEach((key) => store.removeItem(key))
  } catch {
    /* private browsing: nothing was kept */
  }
}

/** Forget one key. */
export function forgetKey(key) {
  try {
    globalThis.localStorage?.removeItem(key)
  } catch {
    /* nothing stored to remove */
  }
}
