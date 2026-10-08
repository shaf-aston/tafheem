import axios from 'axios'

import { profileHeaders } from './lib/profile'

export const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Whose record a request is about goes on every request, read at send time so
// a name switched a moment ago is the one sent. A route that does not care
// ignores it; one that does can no longer be called without it by mistake and
// file a learner's answers under the guest. A call that names someone else
// (sign-up, log-in) keeps its own.
api.interceptors.request.use((config) => {
  for (const [key, value] of Object.entries(profileHeaders())) {
    if (!config.headers.has(key)) config.headers.set(key, value)
  }
  return config
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

const getQuranAyah = (surah, ayah) =>
  api.get(`/quran/${surah}/${ayah}`).then((r) => r.data)

// A printed ayah never changes, so once fetched it is never fetched again.
export const quranAyahQuery = (surah, ayah) => ({
  queryKey: ['quran-ayah', surah, ayah], queryFn: () => getQuranAyah(surah, ayah), retry: false, staleTime: Infinity,
})

// The reading view by default: text and English only. The word-by-word grammar
// is asked for one ayah at a time, because a whole surah of it is ~2MB.
export const getQuranSurah = (surah) =>
  api.get(`/quran/surah/${surah}`).then((r) => r.data)

export const quranSurahQuery = (surah) => ({ queryKey: ['quran-surah', surah], queryFn: () => getQuranSurah(surah) })

// The English of each word, for showing what one word means without leaving the
// page. Its own request, not part of the surah above: it is wanted only where
// the words are drawn separately, and an ayah the two sources disagree about is
// simply absent rather than mis-aligned.
export const getSurahGlosses = (surah) =>
  api.get(`/quran/surah/${surah}/glosses`).then((r) => r.data)

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

// More than one Arabic word: the sense of the whole, then word by word.
export const translateSentence = (q) =>
  api.get('/dictionary/sentence', { params: { q } }).then((r) => r.data)

// What a root has meant since the beginning, as against what a word means today.
// A different book from the dictionary, so a separate call with its own source.
export const getRootMeaning = (root) =>
  api.get('/dictionary/root-meaning', { params: { root } }).then((r) => r.data)

// The باب the root's Form I verb takes, by root so every word on it agrees.
export const rootBabsQuery = (root) => ({
  queryKey: ['root-babs', root],
  queryFn: () => api.get('/dictionary/babs', { params: { root } }).then((r) => r.data),
})

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

// A short AI sentence made only of this learner's learnt words, each one checked.
export const getCheckedSentence = () =>
  api.post('/practice/checked', {}).then((r) => r.data)

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
export const timelinesQuery = {
  queryKey: ['timelines'],
  queryFn: () => api.get('/timelines').then((r) => r.data),
}

// Every dawah topic and question, fetched whole once like timelinesQuery.
export const dawahQuery = {
  queryKey: ['dawah'],
  queryFn: () => api.get('/dawah').then((r) => r.data),
}

// Why the ayahs of one timeline event came down: one line per report. The
// report itself is read from the Qur'an's library like any other book on that
// ayah, so nothing here fetches a megabyte of prose to show a list.
export const asbabQuery = (section, event) => ({
  queryKey: ['timeline-asbab', section, event],
  queryFn: () => api.get(`/timelines/${section}/${event}/asbab`).then((r) => r.data),
})

// Every hadith collection the module can browse or search. Small and fixed,
// fetched once like timelinesQuery.
export const hadithCollectionsQuery = {
  queryKey: ['hadith-collections'],
  queryFn: () => api.get('/hadith/collections').then((r) => r.data),
}

// One collection's books (chapters), each carrying how many hadiths it holds.
export const hadithBooksQuery = (collection) => ({
  queryKey: ['hadith-books', collection],
  queryFn: () => api.get(`/hadith/${collection}/books`).then((r) => r.data),
})

// Opening Hadith: the collections, then every collection's books. Errors stay
// quiet, like prefetchQuery: the panel shows its own when it is opened.
export const hadithOpen = (client) =>
  client.fetchQuery(hadithCollectionsQuery)
    .then((list) => Promise.all(list.map((c) => client.prefetchQuery(hadithBooksQuery(c.id)))))
    .catch(() => {})

// One book's hadiths in full, Arabic and English.
export const hadithBookQuery = (collection, number) => ({
  queryKey: ['hadith-book', collection, number],
  queryFn: () => api.get(`/hadith/${collection}/books/${number}`).then((r) => r.data),
})

// Where each narrator is named in one book's Arabic, and one narrator's sheet.
export const rijalChainsQuery = (collection, book) => ({
  queryKey: ['rijal-chains', collection, book],
  queryFn: () => api.get(`/rijal/chains/${collection}/${book}`).then((r) => r.data),
})
// The narrations sharing one number, each laid against `part`.
export const narrationFamilyQuery = (collection, number, part) => ({
  queryKey: ['rijal-family', collection, number, part],
  queryFn: () => api.get(`/rijal/family/${collection}/${number}`, { params: { part } }).then((r) => r.data),
  retry: false,
})
export const narratorHadithQuery = (id) => ({
  queryKey: ['narrator-hadith', id],
  queryFn: () => api.get(`/rijal/narrators/${id}/hadith`).then((r) => r.data),
})
export const rijalSearchQuery = (q) => ({
  queryKey: ['rijal-search', q],
  queryFn: () => api.get('/rijal/search', { params: { q } }).then((r) => r.data),
})
export const narratorQuery = (id) => ({
  queryKey: ['narrator', id],
  queryFn: () => api.get(`/rijal/narrators/${id}`).then((r) => r.data),
  // No page built for him stays that way, so a 404 is not retried.
  retry: (count, error) => error?.response?.status !== 404 && count < 1,
})

// The sorts of ruling the classical books give (with their plain meaning and count), and the hadith carrying one, a page at a time.
export const usulTermsQuery = {
  queryKey: ['usul-terms'],
  queryFn: () => api.get('/usul/terms').then((r) => r.data),
}
export const usulTermQuery = (kind) => ({
  queryKey: ['usul-term', kind],
  queryFn: ({ pageParam }) => api.get(`/usul/terms/${kind}`, { params: { offset: pageParam } }).then((r) => r.data),
  initialPageParam: 0,
  getNextPageParam: (last, pages) => {
    const seen = pages.reduce((n, p) => n + p.items.length, 0)
    return last.items.length && seen < last.total ? seen : undefined
  },
})

// The narrator list, most hadith first, a page at a time; the server fixes the page size.
export const narratorListQuery = (generation) => ({
  queryKey: ['narrator-list', generation],
  queryFn: ({ pageParam }) => api.get('/rijal/narrators', { params: { generation, offset: pageParam } }).then((r) => r.data),
  initialPageParam: 0,
  getNextPageParam: (last, pages) => {
    const seen = pages.reduce((n, p) => n + p.items.length, 0)
    return last.items.length && seen < last.total ? seen : undefined
  },
})

// Every word typed must appear, in Arabic or English, across the named
// collections; empty collections means every collection, the ordinary case.
export const searchHadith = ({ q, collections = [] }) =>
  api
    .get('/hadith/search', {
      params: { q, collections },
      // One `collections=` per id, the same paramsSerializer findDaleel uses
      // for `books`; left alone, axios writes `collections[]=` and nothing
      // filters.
      paramsSerializer: { indexes: null },
    })
    .then((r) => r.data)

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
export const daleelBooksQuery = {
  queryKey: ['daleel-books'],
  queryFn: () => api.get('/daleel/books').then((r) => r.data),
}

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
// `trial` hears this with the server's trial model instead of the usual ears.
// `signal` lets a reading be given up on. A recitation asks about the same
// recording again as it grows, so a reading already on its way is sometimes
// known to be out of date before it comes back, and on this machine waiting
// for it costs the seconds it takes to read.
// `reading` names this one request, as `X-Reading-Id`, so the server's own
// log and lib/journal.js's trail can be lined up on the same reading.
// Every recording goes to the server this one way. `trial` is sent only when on,
// so a server without a trial model never sees the word.
const postRecording = (path, recording, params, { trial, signal, reading } = {}) => {
  const body = new FormData()
  body.append('audio', recording, 'recitation.webm')
  const asked = new URLSearchParams({ ...params, ...(trial && { trial }) })
  const headers = { 'Content-Type': undefined, ...(reading && { 'X-Reading-Id': reading }) }
  return api.post(`${path}?${asked}`, body, { headers, signal }).then((r) => r.data)
}

export const listen = (recording, { match = false, recite = false, fusha = true, near, before, ...how } = {}) =>
  postRecording('/listen', recording, { match, recite, fusha, ...(near && { near }), ...(before && { before }) }, how)

// How sure the ear is of each word of `check`'s ayahs (as "1:1"), scored from
// the same recording `listen` already wrote `heard` down from. Its own request
// so a slow score never holds back the words a reciter is already reading by;
// see lib/recitingSession.js for how the two are paced against each other.
export const checkReading = (recording, { heard = '', check = [], ...how } = {}) =>
  postRecording('/listen/check', recording, { heard, check: check.join(',') }, how)

// How sure the ear is of each word of `expected`, a phrase that is not an ayah
// (Grow's takbir, tashahhud and the rest), from the same recording `listen`
// wrote `heard` down from. One number per word, in order.
export const checkText = (recording, { heard = '', expected = '', ...how } = {}) =>
  postRecording('/listen/check-text', recording, { heard, expected }, how)

// Grow's paths: the steps to learn and a scholar's words on each.
export const growPathsQuery = {
  queryKey: ['grow-paths'],
  queryFn: () => api.get('/grow/paths').then((r) => r.data),
}

// Where lib/journal.js's trail of reciting events goes. Its own constant
// because sendBeacon cannot go through axios and needs the full path, not
// just what api.post's baseURL would fill in.
export const JOURNAL_PATH = '/api/journal'

// A batch of what reciting did. 204 back, nothing to read, so nothing chains
// off it; lib/journal.js only cares whether the call threw.
export const postJournal = (events) => api.post('/journal', { events })

// The spoken dialects with their unit and lesson titles, and nothing else: the
// Colloquial tab opens on this list and a unit is sixty kilobytes on its own.
export const colloquialQuery = {
  queryKey: ['colloquial'],
  queryFn: () => api.get('/colloquial').then((r) => r.data),
}

// One whole unit, every lesson in it. Sent whole because a learner moves between
// a unit's lessons freely, so paging would only add a wait mid-lesson.
export const colloquialUnitQuery = (dialect, unit) => ({
  queryKey: ['colloquial-unit', dialect, unit],
  queryFn: () => api.get(`/colloquial/${encodeURIComponent(dialect)}/${encodeURIComponent(unit)}`).then((r) => r.data),
})

// One lesson's phrases as every dialect says them, matched by slot.
export const colloquialCompareQuery = (unit, lesson) => ({
  queryKey: ['colloquial-compare', unit, lesson],
  queryFn: () => api.get(`/colloquial/compare/${encodeURIComponent(unit)}/${encodeURIComponent(lesson)}`).then((r) => r.data),
})

// A phrase picture: `file` is the path the lesson names, like "unit-01/greeting.jpg".
export const colloquialImageUrl = (file) =>
  `${api.defaults.baseURL}/colloquial/image/${file.split('/').map(encodeURIComponent).join('/')}`

// Verses that read almost the same as this one (mutashabihat), with the words
// that differ marked. A surah's groups say which ayahs have twins at all.
export const getSimilar = (surah, ayah) =>
  api.get(`/quran/similar/${surah}/${ayah}`).then((r) => r.data)

export const getSimilarSurah = (surah) =>
  api.get(`/quran/similar/surah/${surah}`).then((r) => r.data)
