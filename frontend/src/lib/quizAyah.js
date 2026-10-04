/**
 * The two requests behind the ayah shown under a quiz answer, as react-query
 * options so the panel can prefetch them and the card can read the same cache.
 * The English is Saheeh International in every language: there is no Urdu
 * translation installed.
 */
import { getAyahEditions, getQuranAyah } from '../api'

export const ENGLISH_EDITION = 'saheeh-en'

export const ayahQueries = (surah, ayah) => [
  // A printed ayah never changes, so once fetched it is never fetched again.
  { queryKey: ['quran-ayah', surah, ayah], queryFn: () => getQuranAyah(surah, ayah), retry: false, staleTime: Infinity },
  {
    queryKey: ['ayah-editions', surah, ayah, [ENGLISH_EDITION]],
    queryFn: () => getAyahEditions(surah, ayah, [ENGLISH_EDITION]),
    retry: false,
    staleTime: Infinity,
  },
]
