/**
 * The saved session: places walked, kept across a reload.
 *
 * The only module that reads or writes session.json's store, the way
 * settings.js is for settings. It saves places (`{tab, value}`), never results:
 * an entry can change and is large; a place is a few characters and refetching
 * it always gives the truth.
 *
 * What comes back from storage is untrusted, it can be old, hand-edited, or
 * from a shape this code no longer writes. `parseSession` is the one gate:
 * anything not exactly right is null, and the app opens clean. Pure, so it is
 * tested without a browser. The same bounds gate the save, so a stored record
 * is always one the app itself could have walked.
 */
import config from '../session.json'

const KEY = config['storage-key']
const VERSION = config.version

// A knob that is not a positive number would silently keep every path or drop
// every path. Better to refuse to start than to guess which.
function knob(name) {
  const value = config[name]
  if (!Number.isFinite(value) || value <= 0) throw new Error(`session.json: '${name}' must be a positive number, got ${value}`)
  return value
}
const SHELF_LIFE_MS = knob('shelf-life-hours') * 60 * 60 * 1000
const MAX_STEPS = knob('max-steps')
const MAX_VALUE_LENGTH = knob('max-value-length')
// How many places the trail line shows at once, and how many past searches a
// Recent row keeps. Here rather than in the component because both are knobs
// about where the reader has been, and session.json is where those numbers live.
export const TRAIL_STEPS = knob('trail-steps')
export const RECENT_KEPT = knob('recent-kept')

/** Two places are one place: the same tab opened with the same thing. */
export const samePlace = (a, b) => Boolean(a) && Boolean(b) && a.tab === b.tab && a.value === b.value

const isPlace = (one, tabs) =>
  one !== null && typeof one === 'object'
  && tabs.includes(one.tab)
  && (one.value === null || (typeof one.value === 'string' && one.value.length <= MAX_VALUE_LENGTH))

/**
 * A path the app itself could have walked: within bounds, every step a place
 * on a known tab, and no step repeated straight after itself (visit() never
 * records one, so a record with one was not written by this app).
 */
export function fitsSession(steps, tabs) {
  return Array.isArray(steps) && steps.length > 0 && steps.length <= MAX_STEPS
    && steps.every((one, index) => isPlace(one, tabs) && !samePlace(one, steps[index - 1]))
}

/**
 * A stored record as `{steps, at}`, or null if it is not one of ours, has
 * gone stale, or does not fit the tabs this build has.
 */
export function parseSession(raw, tabs, now) {
  let record
  try {
    record = JSON.parse(raw)
  } catch {
    return null
  }
  if (record?.v !== VERSION) return null
  if (typeof record.saved !== 'number' || now - record.saved > SHELF_LIFE_MS || record.saved > now) return null
  const { steps, at } = record
  if (!fitsSession(steps, tabs)) return null
  if (!Number.isInteger(at) || at < 0 || at >= steps.length) return null
  return { steps: steps.map(({ tab, value }) => ({ tab, value })), at }
}

/** The record as written, for the save below and for tests. */
export const serialise = ({ steps, at }, now) => JSON.stringify({ v: VERSION, saved: now, steps, at })

export function loadSession(tabs, now = Date.now()) {
  try {
    return parseSession(globalThis.localStorage?.getItem(KEY) ?? '', tabs, now)
  } catch {
    return null // private browsing: nothing was kept
  }
}

/** Forget the path. The next load opens on the first tab with nothing in hand. */
export function forgetSession() {
  try {
    globalThis.localStorage?.removeItem(KEY)
  } catch {
    /* private browsing: nothing was kept */
  }
}

/** Save a path, if it is one that would be read back. Beyond the bounds the last good save stands. */
export function saveSession(session, tabs, now = Date.now()) {
  if (!fitsSession(session.steps, tabs)) return
  try {
    globalThis.localStorage?.setItem(KEY, serialise(session, now))
  } catch {
    /* private browsing, the path still holds for this session */
  }
}
