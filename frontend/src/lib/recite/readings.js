/**
 * What a reciting session says about a reading, apart from the session itself: what to tell the reciter
 * when one fails, how recordings and readings are kept, and the view before anything has been said.
 * Pure, so each can be tested without a microphone (recitingSession.test.js).
 */

/**
 * What to tell a reciter when a reading fails, and how to log it: a network
 * drop, a server crash, and a bug in the page after the answer arrived are
 * told apart rather than shown as one grey "did not come back".
 */
export const problemOf = (error) => {
  if (!error?.isAxiosError) {
    return { kind: 'page', text: 'The page failed to show that reading. It has been logged.' }
  }
  // A body that is not the backend's JSON came from the dev proxy, which
  // answers 500 with nothing when the backend is down or restarting.
  const fromProxy = error.response && typeof error.response.data !== 'object'
  if (!error.response || fromProxy) {
    return { kind: 'unreachable', text: "The app's server did not answer. It may be restarting; the next phrase will try again." }
  }
  const detail = error.response.data?.detail
  if (typeof detail === 'string') return { kind: 'server', text: detail }
  return { kind: 'server', text: `The server failed on this reading (error ${error.response.status}).` }
}

/**
 * Keep a recording by its take, dropping the oldest past `max`. A take that is
 * kept again (its reading grew) replaces its blob and keeps its place in line.
 */
export const keepRecording = (store, take, blob, max) => {
  store.set(take, blob)
  while (store.size > max) store.delete(store.keys().next().value)
}

/**
 * Add a reading to the transcript: one entry a recording, in the order the
 * recordings began. A newer reading of a recording replaces its own entry
 * (it holds more of the same sound); nothing is deduped across recordings.
 */
export const addToTranscript = (transcript, window, words) => {
  const at = transcript.findIndex((entry) => entry.window === window)
  if (at === -1) return [...transcript, { window, words }]
  return [...transcript.slice(0, at), { window, words }, ...transcript.slice(at + 1)]
}

/** What a session shows before anything has been said. */
export const EMPTY_VIEW = {
  state: 'idle',
  problem: '',
  // Two halves on purpose: the recordings already finished, and the reading of
  // the one still going. A new reading replaces the second half rather than
  // piling onto it, which is what lets a mark change its mind.
  before: [],
  // Whose words these are, as well as what they are. Recordings overlap: the
  // last reading of one is still being read when the next has begun, and on a
  // slow ear that overlap is most of a recording. Without a name on them, the
  // older recording finishing would clear the newer one's words off the page,
  // and a perfect recitation of al-Fatihah ended with one word showing.
  now: { from: 0, words: [] },
  ended: false,
  // Everything the ear returned while on this page, raw: [{ window, words }],
  // one entry a recording. Not filtered by page, not deduped. For the reciter
  // to read what was heard; the marks above never read it.
  transcript: [],
  // How sure the ear has been of each page word, by its place on the page, in
  // the same two halves. Each is a score, see scores.js. Within a recording the newest reading wins: it holds
  // more of the sound, and an early reading scores words not said yet, up to
  // 0.1 for one word in six (measured on 69 cut recordings), which kept for
  // good would pass that word however it was then said. Across recordings the
  // surer one wins: a word is said once, and one clipped at a recording's
  // edge should not unsay it.
  scores: { before: {}, now: {} },
  // Where in the Qur'an the reciter seems to be, { surah, ayah }, when what
  // they recite is not on this page; null while they are on it.
  elsewhere: null,
  // How many sureness checks are queued or on their way. A page only turns
  // once its own are back, or its last ayah would never be weighed.
  checking: 0,
}
