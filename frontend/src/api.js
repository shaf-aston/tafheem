import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

export const analyzeIraab = (sentence) =>
  api.post('/analyze', { sentence }).then((r) => r.data)

export const analyzeMorphology = ({ word, form }) =>
  api.post('/morphology', { word, form }).then((r) => r.data)

// The meaning is the one field that can come from a network AI call, so it is
// fetched on its own, after the table above is already on screen; never the
// thing the reader waits seconds for.
export const analyzeMeaning = ({ word }) =>
  api.post('/morphology/meaning', { word }).then((r) => r.data)

// Switching باب is the rule engine rebuilding one table, no tagger, no AI, so
// it comes straight back and the rest of the word's answer stays on screen.
export const conjugateForm = ({ root, form }) =>
  api.post('/morphology/conjugate', { root, form }).then((r) => r.data)

export const getQuranAyah = (surah, ayah) =>
  api.get(`/quran/${surah}/${ayah}`).then((r) => r.data)

// The reading view by default: text and English only. The word-by-word grammar
// is asked for one ayah at a time, because a whole surah of it is ~2MB.
export const getQuranSurah = (surah) =>
  api.get(`/quran/surah/${surah}`).then((r) => r.data)

// The English of each word, for showing what one word means without leaving the
// page. Its own request, not part of the surah above: it is wanted only where
// the words are drawn separately, and an ayah the two sources disagree about is
// simply absent rather than mis-aligned.
export const getSurahGlosses = (surah) =>
  api.get(`/quran/surah/${surah}/glosses`).then((r) => r.data.ayahs)

// How the ayah's words join into one another. Derived from the corpus tags by
// rule, so it comes back with its own source label; not the corpus's.
/**
 * Which books are installed, in the order the library names them. Asked once
 * for the whole session: this changes only when the import script is run, which
 * cannot happen while the app is up.
 */
export const getQuranEditions = (kind = '') =>
  api.get('/quran/editions', { params: kind ? { kind } : {} }).then((r) => r.data)

/**
 * What the named books say about one ayah. `ids` blank means every book, which
 * is not what a panel wants: a long commentary runs to thousands of words, so
 * the panel asks for the one book it is showing and lets the cache keep the
 * others once they have been read.
 */
export const getSurahEdition = (surah, id) =>
  api.get(`/quran/editions/surah/${surah}`, { params: { id } }).then((r) => r.data)

export const getAyahEditions = (surah, ayah, ids = []) =>
  api
    .get(`/quran/editions/${surah}/${ayah}`, ids.length ? { params: { ids: ids.join(',') } } : {})
    .then((r) => r.data)

export const getQuranTarkeeb = (surah, ayah) =>
  api.get(`/quran/${surah}/${ayah}/tarkeeb`).then((r) => r.data)

export const searchQuran = (q) =>
  api.get('/quran/search', { params: { q } }).then((r) => r.data)

export const getQuranRoot = (root) =>
  api.get(`/quran/root/${encodeURIComponent(root)}`).then((r) => r.data)

// The worked examples from the Nahw books. Small, fixed, and fetched once.
export const getTarkeebExamples = () =>
  api.get('/tarkeeb/examples').then((r) => r.data)

export const searchDictionary = (q, lang = 'ar') =>
  api.get('/dictionary/search', { params: { q, lang } }).then((r) => r.data)

// What a root has meant since the beginning, as against what a word means today.
// A different book from the dictionary, so a separate call with its own source.
export const getRootMeaning = (root) =>
  api.get('/dictionary/root-meaning', { params: { root } }).then((r) => r.data)

// Whole entries for a root, from every classical dictionary that has one. Its
// own call, and asked for only when the shelf is opened: four whole entries run
// to a hundred kilobytes, which is not worth fetching for a reader who came to
// look up one word.
export const getLexicons = (root) =>
  api.get('/dictionary/lexicons', { params: { root } }).then((r) => r.data)

// The same entry retold in English by a model. Its own call because it costs
// one to make: nothing asks for it until a reader presses the button.
export const getRootEntryEnglish = (root) =>
  api.get('/dictionary/root-meaning/english', { params: { root } }).then((r) => r.data)

// The same entry again, paired: one English line under each Arabic line. The
// backend does the pairing and refuses an answer it could not line up, so
// whatever arrives here is safe to print interleaved.
export const getRootEntryLines = (root) =>
  api.get('/dictionary/root-meaning/english/lines', { params: { root } }).then((r) => r.data)

export const generatePractice = (sentence) =>
  api.post('/practice', { sentence }).then((r) => r.data)

// The teacher's exercise library: every tag, every exercise, and a count per
// tag. Small and fixed, so it is fetched whole once and filtered on the
// frontend rather than re-asked per tag.
export const getTamreen = () =>
  api.get('/tamreen').then((r) => r.data)

// The teacher's Nahw notes, every topic whole. Fixed for the life of the
// backend and hidden on the page, never here, so it is fetched once.
export const getNotes = () =>
  api.get('/notes').then((r) => r.data)

// The teacher's own page a note was read from, for an <img> or a link, so it
// is an address rather than a request.
export const notePageUrl = (topicId, page) =>
  `${api.defaults.baseURL}/notes/${encodeURIComponent(topicId)}/page/${Number(page)}.png`

// Every timeline section with its places and sources. About fifty events, fixed
// for the life of the backend, so it is fetched whole once and filtered here.
export const getTimelines = () =>
  api.get('/timelines').then((r) => r.data)

// Why the ayahs of one timeline event came down: one line per report. The
// report itself is read from the Qur'an's library like any other book on that
// ayah, so nothing here fetches a megabyte of prose to show a list.
export const getTimelineAsbab = (section, event) =>
  api.get(`/timelines/${section}/${event}/asbab`).then((r) => r.data)

export const healthCheck = () =>
  api.get('/health').then((r) => r.data)

// Everything the app is built on. Fixed for the life of the backend, so it is
// asked for once and kept, the footer on every tab reads the same answer.
export const getSources = () =>
  api.get('/sources').then((r) => r.data.sources)

// Find the quotation. One question in, passages out; the backend never answers
// the question, so nothing here has an answer field to render. `books` narrows
// it to those books by name; empty is every book, which is the ordinary case.
export const findDaleel = ({ q, books = [] }) =>
  api
    .get('/daleel', {
      params: { q, books },
      // One `books=` per book. Left alone, axios writes `books[]=` and the
      // backend reads no books at all, so every filtered search quietly
      // searched the whole library instead.
      paramsSerializer: { indexes: null },
    })
    .then((r) => r.data)

// Which books the search can be narrowed to. Read from the built index, so a
// book is only offered if searching it would actually find something.
export const getDaleelBooks = () =>
  api.get('/daleel/books').then((r) => r.data)

// A recording, and what was said. `match` also asks which ayahs those words
// were, which only the Qur'an tab wants; Daleel just searches the words. Sent as
// a file rather than JSON because audio is not text and base64 would be a third
// larger for nothing. The Content-Type is left to the browser on purpose: it has
// to add the multipart boundary itself.
// How sure the ear is of each word is a separate question, `checkReading`
// below, never asked here: a slow score must never hold back the words a
// reciter is already reading by.
// `signal` lets a reading be given up on. A recitation asks about the same
// recording again as it grows, so a reading already on its way is sometimes
// known to be out of date before it comes back, and on this machine waiting
// for it costs the seconds it takes to read.
// `reading` names this one request, as `X-Reading-Id`, so the server's own
// log and lib/journal.js's trail can be lined up on the same reading.
export const listen = (recording, { match = false, recite = false, fusha = true, signal, reading } = {}) => {
  const body = new FormData()
  body.append('audio', recording, 'recitation.webm')
  const asked = new URLSearchParams({ match, recite, fusha })
  const headers = { 'Content-Type': undefined }
  if (reading) headers['X-Reading-Id'] = reading
  return api.post(`/listen?${asked}`, body, { headers, signal })
    .then((r) => r.data)
}

// How sure the ear is of each word of `check`'s ayahs (as "1:1"), scored from
// the same recording `listen` already wrote `heard` down from. Its own request
// so a slow score never holds back the words a reciter is already reading by;
// see lib/recitingSession.js for how the two are paced against each other.
export const checkReading = (recording, { heard = '', check = [], signal, reading } = {}) => {
  const body = new FormData()
  body.append('audio', recording, 'recitation.webm')
  const asked = new URLSearchParams({ heard, check: check.join(',') })
  const headers = { 'Content-Type': undefined }
  if (reading) headers['X-Reading-Id'] = reading
  return api.post(`/listen/check?${asked}`, body, { headers, signal })
    .then((r) => r.data)
}

// Where lib/journal.js's trail of reciting events goes. Its own constant
// because sendBeacon cannot go through axios and needs the full path, not
// just what api.post's baseURL would fill in.
export const JOURNAL_PATH = '/api/journal'

// A batch of what reciting did. 204 back, nothing to read, so nothing chains
// off it; lib/journal.js only cares whether the call threw.
export const postJournal = (events) => api.post('/journal', { events })
