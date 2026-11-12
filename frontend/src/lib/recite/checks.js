/**
 * The sureness checks a session sends: queued, then sent one at a time, each given up on if the ear does
 * not answer. Words never wait on this; a check is only ever fired and forgotten from the session's send().
 */
import config from '../../config/recite.json'
import { problemOf } from './readings'

const CHECK_TIMEOUT_MS = config['check-timeout-s'] * 1000
const CHECK_QUEUE_MAX = config['check-queue-max']

/**
 * What a newly-finished words reading does to the sureness checks waiting to
 * be sent: at most one is ever in flight (the session's own runner enforces
 * that), so this is only about what waits.
 *
 * A queued job not yet sent is replaced by a newer one for the same recording,
 * latest wins, because a later reading holds more of the sound; two identical
 * jobs queued back to back collapse the same way, to one. A job already sent
 * is left alone, the same choice already made for words: nothing here aborts
 * an in-flight check for a newer one. A different recording's job is never
 * touched, so recordings are checked in the order they finished, even a
 * recording's own final check past a later recording's first.
 *
 * Past `max` entries the oldest not-yet-sent job is dropped to make room: a
 * check nobody has asked for yet is worth less than one already on its way,
 * so the in-flight job at the front, when it is sent, is never the one
 * dropped. Returns the dropped job too, so the caller can journal it.
 */
export const queueCheck = (queue, job, max) => {
  const at = queue.findIndex((q) => q.window === job.window && !q.sent)
  const next = at === -1 ? [...queue, job] : [...queue.slice(0, at), job, ...queue.slice(at + 1)]
  if (next.length <= max) return { queue: next, dropped: null }
  const drop = next.findIndex((q) => !q.sent)
  if (drop === -1) return { queue: next, dropped: null }
  return { queue: [...next.slice(0, drop), ...next.slice(drop + 1)], dropped: next[drop] }
}


/**
 * The queue itself. `checkReading` and `note` are the session's own (so tests can script them);
 * `sessionId()` and `tuned()` read the newest value when needed; `onCount(n)` is told how many are waiting
 * or on their way. Returns `enqueue(job)`, `turn()` (a page turned: the one in flight is given up on as
 * turned, the unsent are dropped) and `reset()` (a new recitation: nothing of the last one stays).
 */
export function createCheckQueue({ checkReading, note, sessionId, tuned, onCount }) {
  let checkQueue = []
  let checkBusy = false

  /**
   * Send the front of the queue, if the ear is free and there is one. A
   * check that does not answer within check-timeout-s is given up on rather
   * than left to hold checkBusy true forever: the abort is the job's own,
   * held so start() can also give up on it when a new session begins.
   */
  const pump = () => {
    if (checkBusy) return
    const job = checkQueue[0]
    if (!job) return
    checkBusy = true
    job.sent = true
    job.abort = new AbortController()
    const timer = setTimeout(() => job.abort.abort(), CHECK_TIMEOUT_MS)
    note('check.sent', { session: sessionId(), reading: job.reading })
    checkReading(job.blob, { heard: job.heard, check: job.ayahs, tuned: tuned(), reading: job.reading, signal: job.abort.signal })
      .then(({ sure, detail }) => {
        note('check.answered', { session: sessionId(), reading: job.reading })
        job.apply(sure, detail)
      })
      .catch((error) => {
        if (job.abort.signal.aborted) {
          note('check.failed', { session: sessionId(), reading: job.reading, kind: job.turned ? 'turned' : 'timeout' })
          return
        }
        const { text } = problemOf(error)
        note('check.failed', { session: sessionId(), reading: job.reading, message: text })
      })
      .finally(() => {
        clearTimeout(timer)
        checkQueue = checkQueue.slice(1)
        checkBusy = false
        onCount(checkQueue.length)
        pump()
      })
  }

  /** Queue a sureness check, replacing a still-queued one for the same recording. */
  const enqueue = (job) => {
    const was = checkQueue
    const { queue: next, dropped } = queueCheck(was, job, CHECK_QUEUE_MAX)
    if (dropped) {
      note('check.dropped', { session: sessionId(), reading: dropped.reading })
    } else if (next.length === was.length) {
      // A queued job that was replaced in place never gets sent; say so.
      const at = next.findIndex((q, i) => q !== was[i])
      if (at !== -1) note('check.aborted', { session: sessionId(), reading: was[at].reading })
    }
    checkQueue = next
    onCount(checkQueue.length)
    pump()
  }

  return {
    enqueue,
    turn() {
      const inFlight = checkQueue.find((q) => q.sent)
      if (inFlight) { inFlight.turned = true; inFlight.abort?.abort() }
      checkQueue = checkQueue.filter((q) => q.sent)
    },
    reset() {
      checkQueue[0]?.abort?.abort()
      checkQueue = []
    },
    count: () => checkQueue.length,
  }
}
