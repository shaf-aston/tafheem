/**
 * A trail of what reciting did, sent to the server in small batches.
 *
 * Best-effort only: an event that cannot be sent is dropped, never retried,
 * and nothing here ever throws or waits on reciting itself. Read by
 * lib/recitingSession.js; api.js stays the only place that knows the URL.
 */
import { JOURNAL_PATH, postJournal } from '../api'
import config from '../recite.json'

const FLUSH_MS = config['journal-flush-ms']
const BATCH = config['journal-batch']
const QUEUE_MAX = config['journal-queue-max']

let queue = []
let dropped = 0

/** The first `max` events of `queue`, in order; an exact duplicate is kept, not folded away. */
export const batchOf = (queue, max) => queue.slice(0, max)

const post = (events, beacon) => {
  if (beacon && typeof navigator !== 'undefined' && navigator.sendBeacon) {
    navigator.sendBeacon(JOURNAL_PATH, JSON.stringify({ events }))
    return Promise.resolve()
  }
  return postJournal(events)
}

/** Send whatever is queued, in batches of `journal-batch`. Never throws. */
async function flush(beacon = false) {
  while (queue.length) {
    const batch = batchOf(queue, BATCH)
    queue = queue.slice(batch.length)
    try {
      await post(batch, beacon)
    } catch {
      // A batch that fails to send is not retried; the next tick has fresher events anyway.
    }
  }
}

/**
 * Queue one event. `fields.session` and `fields.reading` are the ids it
 * belongs to; anything else in `fields` becomes `detail`. Never throws.
 */
export function note(kind, fields = {}) {
  try {
    const { session, reading, ...detail } = fields
    const event = { at: new Date().toISOString(), kind }
    // Left out when blank: the server refuses a blank id, and one bad event
    // throws away the whole batch it came in.
    if (session) event.session = session
    if (reading) event.reading = reading
    if (Object.keys(detail).length) event.detail = detail
    if (queue.length >= QUEUE_MAX) {
      dropped += 1
    } else {
      queue.push(event)
      if (dropped && queue.length < QUEUE_MAX) {
        queue.push({ at: new Date().toISOString(), kind: 'journal.dropped', detail: { count: dropped } })
        dropped = 0
      }
    }
    if (queue.length >= BATCH) flush()
  } catch {
    // Journalling a recitation must never be the reason it stops.
  }
}

// Flushed on a timer, and again right before the page is gone: the timer
// alone would lose whatever was queued in the last flush-ms of a session.
// Guarded for a test environment with no window: nothing here should run cold.
if (typeof window !== 'undefined') {
  setInterval(() => flush(false), FLUSH_MS)
  const onHide = () => flush(true)
  window.addEventListener('pagehide', onHide)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') onHide()
  })
}
