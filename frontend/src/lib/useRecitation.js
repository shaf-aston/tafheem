/**
 * When each word is recited, so a word can be lit as it is read aloud.
 *
 * A recording is only a sound file; nothing in it says where one word ends and
 * the next begins. Those times have to be measured, and api.quran.com has them
 * for every one of our reciters, free and with no key or account. One request
 * per surah, about 35KB, and it carries the audio address as well as the times.
 *
 * That pairing is the whole point. A list of word times is true of exactly one
 * recording of a recitation, not of the recitation in general: another site's
 * copy of the same reciter may be trimmed differently and every word would land
 * late. So the address played is the address the times came back with, and where
 * they did not come back at all the EveryAyah recording is played as before and
 * no word is lit. A word never lights on a guess.
 */
import { useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'

import config from '../data/reciters.json'
import { RECITERS, ayahAudioUrl } from './ayahAudio'

/** The measured times for one whole surah, keyed by ayah. */
async function fetchRecitation(surah, reciterId) {
  const reciter = RECITERS.find((r) => r.id === reciterId) ?? RECITERS[0]
  const url = config.timings_url
    .replace('{reciter}', reciter.quran_id)
    .replace('{surah}', surah)
  try {
    const response = await fetch(url)
    if (!response.ok) throw new Error(`Recitation timings: ${response.status}`)

    const { audio_files: files = [] } = await response.json()
    const byAyah = {}
    for (const file of files) {
      const [, ayah] = file.verse_key.split(':')
      byAyah[Number(ayah)] = {
        // A protocol-relative address comes back for some reciters; a bare path
        // for the rest. Both have to end up absolute.
        url: file.url.startsWith('http') ? file.url
          : file.url.startsWith('//') ? `https:${file.url}`
            : config.audio_host + file.url,
        segments: file.segments ?? [],
      }
    }
    return byAyah
  } catch (error) {
    // The page stays silent either way - no word lights without measured
    // segments - but a real failure here should not be invisible to whoever
    // is debugging why nothing is lighting.
    console.error('Recitation timings fetch failed:', error)
    throw error
  }
}

/**
 * One surah's recitation in one reciter's voice.
 *
 * `urlFor(ayah)` is what to play, always answerable: the measured recording once
 * it is known, the EveryAyah one until then. `segmentsFor(ayah)` is empty unless
 * the two agree, which is what stops a word being lit against the wrong file.
 */
export function useRecitation(surah, reciterId) {
  const { data } = useQuery({
    queryKey: ['recitation', surah, reciterId],
    queryFn: () => fetchRecitation(surah, reciterId),
    // Measured once and printed; it will not change while the page is open.
    staleTime: Infinity,
    // A silent, optional improvement. Failing it must never make a page noisy.
    retry: 1,
  })

  const urlFor = useCallback(
    (ayah) => data?.[ayah]?.url ?? ayahAudioUrl(surah, ayah, reciterId),
    [data, surah, reciterId],
  )

  const segmentsFor = useCallback((ayah) => data?.[ayah]?.segments ?? [], [data])

  return { urlFor, segmentsFor }
}

/**
 * Which word is being recited at this moment, counting from zero, or -1.
 *
 * A segment is [order, word, starts at, ends in], all in milliseconds. Words are
 * numbered from one in the corpus and drawn from zero on the page, hence the
 * step down. A moment between two words, the breath in the middle of an ayah,
 * lights nothing rather than holding the last word lit, which would say the
 * reciter is still on a word he has finished.
 */
export function wordAt(segments, ms) {
  for (const [, word, from, until] of segments) {
    if (ms >= from && ms < until) return word - 1
  }
  return -1
}
