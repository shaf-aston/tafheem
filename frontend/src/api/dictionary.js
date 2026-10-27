// The dictionary: words, whole sentences, roots and the classical lexicons.
import { api } from './client'

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
