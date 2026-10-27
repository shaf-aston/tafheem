// The Qur'an: ayah and surah text, mushaf pages, the books on an ayah, search, roots.
import { api } from './client'

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

/** The printed mushafs a surah can be read in as pages; empty until one is built. */
export const mushafsQuery = { queryKey: ['mushafs'], queryFn: () => api.get('/quran/mushaf').then((r) => r.data), staleTime: Infinity }

/** A surah as one printing's pages, each whole page it is on. */
export const mushafPagesQuery = (printing, surah) => ({
  queryKey: ['mushaf-pages', printing, surah],
  queryFn: () => api.get(`/quran/mushaf/${printing}/surah/${surah}`).then((r) => r.data),
  staleTime: Infinity,
})

// The English of each word, for showing what one word means without leaving the
// page. Its own request, not part of the surah above: it is wanted only where
// the words are drawn separately, and an ayah the two sources disagree about is
// simply absent rather than mis-aligned.
const getSurahGlosses = (surah) =>
  api.get(`/quran/surah/${surah}/glosses`).then((r) => r.data)
export const surahGlossesQuery = (surah) => ({ queryKey: ['surah-glosses', surah], queryFn: () => getSurahGlosses(surah) })

/**
 * Which books are installed, in the order the library names them. Asked once
 * for the whole session: this changes only when the import script is run, which
 * cannot happen while the app is up.
 */
export const getQuranEditions = (kind = '') =>
  api.get('/quran/editions', { params: kind ? { kind } : {} }).then((r) => r.data)
export const translationsQuery = { queryKey: ['quran-editions', 'translation'], queryFn: () => getQuranEditions('translation') }

/**
 * What the named books say about one ayah. `ids` blank means every book, which
 * is not what a panel wants: a long commentary runs to thousands of words, so
 * the panel asks for the one book it is showing and lets the cache keep the
 * others once they have been read.
 */
const getSurahEdition = (surah, id) =>
  api.get(`/quran/editions/surah/${surah}`, { params: { id } }).then((r) => r.data)
export const surahEditionQuery = (surah, id) => ({ queryKey: ['surah-edition', surah, id], queryFn: () => getSurahEdition(surah, id) })

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
