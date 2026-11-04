// Reciting: the recording goes up, the words and how sure the ear is come back.
import { api } from './client'

// A recording, and what was said. `match` also asks which ayahs those words
// were, which only the Qur'an tab wants; Daleel just searches the words. `near`,
// the open page as "2:1-2:5", asks where in the whole Qur'an they were; `before`,
// the last reading whose place was not sure, is placed together with it. Sent as
// a file rather than JSON because audio is not text and base64 would be a third
// larger for nothing. The Content-Type is left to the browser on purpose: it has
// to add the multipart boundary itself.
// How sure the ear is of each word is a separate question, `checkReading`
// below, never asked here: a slow score must never hold back the words a
// reciter is already reading by.
// `tuned` is for the two checks below: they score with the server's tuned model.
// A reading is always written down by the usual ears, quick first.
// `signal` lets a reading be given up on. A recitation asks about the same
// recording again as it grows, so a reading already on its way is sometimes
// known to be out of date before it comes back, and on this machine waiting
// for it costs the seconds it takes to read.
// `reading` names this one request, as `X-Reading-Id`, so the server's own
// log and lib/recite/journal.js's trail can be lined up on the same reading.
// Every recording goes to the server this one way. `tuned` is sent only when on,
// so a server without a tuned model never sees the word.
const postRecording = (path, recording, params, { tuned, signal, reading } = {}) => {
  const body = new FormData()
  body.append('audio', recording, 'recitation.webm')
  const asked = new URLSearchParams({ ...params, ...(tuned && { tuned }) })
  const headers = { 'Content-Type': undefined, ...(reading && { 'X-Reading-Id': reading }) }
  return api.post(`${path}?${asked}`, body, { headers, signal }).then((r) => r.data)
}

export const listen = (recording, { match = false, recite = false, fusha = true, near, before, signal, reading } = {}) =>
  postRecording('/listen', recording, { match, recite, fusha, ...(near && { near }), ...(before && { before }) }, { signal, reading })

// How sure the ear is of each word of `check`'s ayahs (as "1:1"), scored from
// the same recording `listen` already wrote `heard` down from. Its own request
// so a slow score never holds back the words a reciter is already reading by;
// see lib/recite/recitingSession.js for how the two are paced against each other.
export const checkReading = (recording, { heard = '', check = [], ...how } = {}) =>
  postRecording('/listen/check', recording, { heard, check: check.join(',') }, how)

// Where lib/recite/journal.js's trail of reciting events goes. Its own constant
// because sendBeacon cannot go through axios and needs the full path, not
// just what api.post's baseURL would fill in.
export const JOURNAL_PATH = '/api/journal'

// A batch of what reciting did. 204 back, nothing to read, so nothing chains
// off it; lib/recite/journal.js only cares whether the call threw.
export const postJournal = (events) => api.post('/journal', { events })
