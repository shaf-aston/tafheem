// Similar verses (mutashabihat).
import { api } from './client'

// Verses that read almost the same as this one (mutashabihat), with the words
// that differ marked. A surah's groups say which ayahs have twins at all.
const getSimilar = (surah, ayah) =>
  api.get(`/quran/similar/${surah}/${ayah}`).then((r) => r.data)

const getSimilarSurah = (surah) =>
  api.get(`/quran/similar/surah/${surah}`).then((r) => r.data)

// The same two as queries, one key each wherever they are read or fetched ahead.
export const similarSurahQuery = (surah) => ({
  queryKey: ['similar-surah', Number(surah)],
  queryFn: () => getSimilarSurah(surah),
})

export const similarAyahQuery = (key) => {
  const [surah, ayah] = key.split(':')
  return { queryKey: ['similar', surah, ayah], queryFn: () => getSimilar(surah, ayah), staleTime: Infinity }
}
