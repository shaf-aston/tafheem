import { useEffect, useRef, useSyncExternalStore } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { quranSurahQuery, surahGlossesQuery } from '../../api'
import { warm } from '../warm'
import { useTranslation } from '../useTranslation'
import { useRecitation } from './useRecitation'
import { RECITERS, nowPlaying, watch } from '../ayahAudio'
import { LAST_SURAH } from '../surahRef'
import { useRemembered, useRememberedFlag } from '../useRemembered'
import { useLearntLemmas } from './useLearntLemmas'
import { PHONE, useMedia } from '../useMedia'

const TOUCH = '(pointer: coarse)'

/**
 * What the Quran reader reads one surah with: its text, the English of each
 * word, the translation, the recitation, and the reader's own choices about
 * them.
 *
 * One request brings the surah's text and its English, 35ms for al-Baqarah,
 * the longest. The word-by-word grammar is not fetched here: it is ~2MB for a
 * long surah and is only worth loading for the ayah being studied.
 *
 * One reciter and one recitation for the whole view, held here: the bar plays
 * by them and every row lights its words by them, so the two cannot disagree
 * about which recording is sounding.
 */
export function useSurahReading(surah) {
  const [reciter, chooseReciter] = useRemembered('reciter', RECITERS.map((one) => one.id))

  const { data, isPending, isError, error, refetch } = useQuery(quranSurahQuery(surah))
  const client = useQueryClient()
  useEffect(() => {
    if (surah < LAST_SURAH) warm(client, quranSurahQuery(surah + 1))
  }, [client, surah])

  // The English of each word, for the hover gloss. Its own request so the text
  // is never held up by it, and reads normally for good if it never arrives.
  const { data: glosses } = useQuery(surahGlossesQuery(surah))
  const learnt = useLearntLemmas()
  const [allMeanings, showAllMeanings] = useRememberedFlag('reader-all-meanings', false)
  const anyGlosses = Object.keys(glosses?.ayahs ?? {}).length > 0
  // Reading without touching the words: a switch in the bar, which the reader
  // may take out of the bar, and which is off whenever it is out of reach.
  const touch = useMedia(TOUCH)
  const phone = useMedia(PHONE)
  const [noTouchButton, showNoTouchButton] = useRememberedFlag('reader-no-touch-button', true)
  const [noTouchOn, setNoTouch] = useRememberedFlag('reader-no-touch', false)
  const noTouch = touch && noTouchButton && noTouchOn
  const recitation = useRecitation(surah, reciter)
  // The bar stays away until something is recited; the header's play starts it.
  const reciting = useSyncExternalStore(watch, nowPlaying, () => '') !== ''
  const recite = useRef(null)
  const translation = useTranslation(surah)

  return {
    data, isPending, isError, error, refetch,
    glosses, learnt, allMeanings, showAllMeanings, anyGlosses,
    touch, phone, noTouchButton, showNoTouchButton, noTouchOn, setNoTouch, noTouch,
    reciter, chooseReciter, recitation, reciting, recite, translation,
  }
}
