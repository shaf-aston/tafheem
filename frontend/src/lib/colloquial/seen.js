/**
 * Which topics this device has opened, and the last one: so the list can say where you were
 * and what you have been through. Kept in the browser, per device, because phrase practice
 * is not filed to the learner's record (only word drills are, lib/colloquial/wordPractice.js),
 * so "opened" is the one honest thing every topic can show.
 *
 * A topic is `dialect/unit/lesson`; the last place is as lib/colloquial/place.js writes it
 * (with `/words` where the words were open), so it can be parsed back to a place. Storage may
 * be refused (a private window): then it lasts the visit and nothing breaks.
 */
import { useSyncExternalStore } from 'react'

const KEY = 'colloq-seen'
const EMPTY = { last: null, seen: [] }

function load() {
  try {
    const stored = JSON.parse(globalThis.localStorage?.getItem(KEY) ?? 'null')
    return {
      last: typeof stored?.last === 'string' ? stored.last : null,
      seen: Array.isArray(stored?.seen) ? stored.seen.filter((s) => typeof s === 'string') : [],
    }
  } catch {
    return EMPTY
  }
}

let state = load()
const listeners = new Set()

/** The topic a place string is in, or null above topic level. */
export const topicOf = (place) => {
  const parts = place?.split('/') ?? []
  return parts.length >= 3 ? parts.slice(0, 3).join('/') : null
}

/** Note that `place` was opened. Above topic level it changes nothing. */
export function markSeen(place) {
  const topic = topicOf(place)
  if (!topic) return
  const seen = state.seen.includes(topic) ? state.seen : [...state.seen, topic]
  state = { last: place, seen }
  try { globalThis.localStorage?.setItem(KEY, JSON.stringify(state)) } catch { /* kept for this visit only */ }
  listeners.forEach((tell) => tell())
}

/** How many of a unit's topics were opened. */
export const seenInUnit = (record, dialect, unit) => record.seen.filter((t) => t.startsWith(`${dialect}/${unit}/`)).length

/** "6 topics", or how many of them were opened: "3 of 6 topics seen". */
export const topicsNote = (total, done = 0) => (done ? `${done} of ${total} topics seen` : `${total} topics`)

export const isSeen = (record, dialect, unit, lesson) => record.seen.includes(`${dialect}/${unit}/${lesson}`)

/** The record, re-read by whoever draws from it when a topic is opened. */
export const useSeen = () => useSyncExternalStore(
  (tell) => { listeners.add(tell); return () => listeners.delete(tell) },
  () => state,
  () => state,
)

/** For tests: forget everything, in memory and in storage. */
export function forgetSeen() {
  state = EMPTY
  try { globalThis.localStorage?.removeItem(KEY) } catch { /* nothing kept */ }
  listeners.forEach((tell) => tell())
}
