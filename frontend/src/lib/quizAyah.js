/**
 * The two requests behind the ayah shown under a quiz answer, as react-query
 * options so the panel can prefetch them and the card can read the same cache.
 * The English is Saheeh International in every language: there is no Urdu
 * translation installed.
 */
import { getAyahEditions, quranAyahQuery } from '../api'

export const ENGLISH_EDITION = 'saheeh-en'

export const ayahQueries = (surah, ayah) => [
  quranAyahQuery(surah, ayah),
  {
    queryKey: ['ayah-editions', surah, ayah, [ENGLISH_EDITION]],
    queryFn: () => getAyahEditions(surah, ayah, [ENGLISH_EDITION]),
    retry: false,
    staleTime: Infinity,
  },
]
