/**
 * Opening the Qur'an tab: what its reader asks for on the place it was last
 * on, fetched on idle like every other tab's opening data (App.jsx openTab).
 * The surah, its word glosses, the list of translations and the chosen
 * translation's text, all at once. Nothing when there is no place: the tab
 * then opens on its search box, which needs nothing from the server.
 */
import { quranSurahQuery, surahEditionQuery, surahGlossesQuery, translationsQuery } from '../api'
import { lastPlaceOn } from './journey'
import { readRaw } from './stored'
import { editionFor } from './useTranslation'

const AYAH_REF = /^(\d+):(\d+)$/

export function quranOpen(client, place = lastPlaceOn('quran')) {
  const address = AYAH_REF.exec(place ?? '')
  if (!address) return undefined
  const surah = Number(address[1])
  const edition = editionFor(readRaw('translation-edition'), null)
  return Promise.all([
    client.prefetchQuery(quranSurahQuery(surah)),
    client.prefetchQuery(surahGlossesQuery(surah)),
    client.prefetchQuery(translationsQuery),
    client.prefetchQuery(surahEditionQuery(surah, edition)),
  ])
}
