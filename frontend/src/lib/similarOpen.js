/**
 * Opening the Similar tab: the surah it was last on and the pair it opens on,
 * fetched on idle like every other tab's opening data (App.jsx openTab). The
 * pair needs the surah's list to be known, so the two go one after the other
 * here, ahead of the tap, instead of one after the other once the tab is open.
 */
import { similarAyahQuery, similarSurahQuery } from '../api'
import copy from '../config/similar.json'
import { lastPlaceOn } from './journey'
import { firstPair, pairsOf } from './similar'
import { parsePlace } from './similarPlace'
import { readRaw } from './stored'

export const SURAH_KEY = 'similar-surah'

/** The surah the tab shows with no verse asked: the remembered one, else similar.json's. */
export const rememberedSurah = () => {
  const n = Number(readRaw(SURAH_KEY))
  return Number.isInteger(n) && n >= 1 && n <= 114 ? n : copy['default-surah']
}

export function similarOpen(client, place = lastPlaceOn('similar')) {
  const asked = parsePlace(place)
  const surah = asked?.surah ?? rememberedSurah()
  const wanted = asked && `${asked.surah}:${asked.ayah}`
  return client.fetchQuery(similarSurahQuery(surah))
    .then((data) => {
      const pair = firstPair(pairsOf(data, surah), wanted)
      return pair && client.prefetchQuery(similarAyahQuery(pair.mine))
    })
    .catch(() => {})
}
