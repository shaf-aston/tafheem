// Grammar: the i'raab and sarf analysers, the practice they make, the teacher's notes and tamreen.
import { api } from './client'

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

// The worked examples from the Nahw books. Small, fixed, and fetched once.
export const getTarkeebExamples = () =>
  api.get('/tarkeeb/examples').then((r) => r.data)

export const generatePractice = (sentence) =>
  api.post('/practice', { sentence }).then((r) => r.data)

// A short AI sentence made only of this learner's learnt words, each one checked.
export const makeCheckedSentence = () =>
  api.post('/practice/checked', {}).then((r) => r.data)

export const getTamreen = () =>
  api.get('/tamreen').then((r) => r.data)

// The teacher's Nahw notes, every topic whole. Fixed for the life of the
// backend and hidden on the page, never here, so it is fetched once.
const getNotes = () =>
  api.get('/notes').then((r) => r.data)
export const notesQuery = { queryKey: ['notes'], queryFn: getNotes }

// The teacher's own page a note was read from, for an <img> or a link, so it
// is an address rather than a request.
export const notePageUrl = (topicId, page) =>
  `${api.defaults.baseURL}/notes/${encodeURIComponent(topicId)}/page/${Number(page)}.png`
