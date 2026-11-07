/**
 * Opening the Qur'an tab: what its reader asks for on the place it was last
 * on, fetched on idle like every other tab's opening data (App.jsx openTab).
 * The surah, its word glosses, the list of translations and the chosen
 * translation's text, all at once. With no place the tab opens on today's
 * ayah (components/quran/QuranOpening), so that one ayah and its English.
 */
import { quranSurahQuery, surahEditionQuery, surahGlossesQuery, translationsQuery } from '../../api'
import { lastPlaceOn } from '../nav/journey'
import { readRaw } from '../store/stored'
import { AYAH_REF } from './surahRef'
import { editionFor } from '../similar/useTranslation'
import { ayahQueries } from '../quiz/quizAyah'
import { todayAyah } from './todayAyah'

export function quranOpen(client, place = lastPlaceOn('quran')) {
  const address = AYAH_REF.exec(place ?? '')
  if (!address) {
    const today = todayAyah()
    return Promise.all(ayahQueries(today.surah, today.ayah).map((query) => client.prefetchQuery(query)))
  }
  const surah = Number(address[1])
  const edition = editionFor(readRaw('translation-edition'), null)
  return Promise.all([
    client.prefetchQuery(quranSurahQuery(surah)),
    client.prefetchQuery(surahGlossesQuery(surah)),
    client.prefetchQuery(translationsQuery),
    client.prefetchQuery(surahEditionQuery(surah, edition)),
  ])
}
