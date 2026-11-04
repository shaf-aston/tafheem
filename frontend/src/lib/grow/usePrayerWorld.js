/** The Prayer world: the words said in salah, from /api/grow/worlds/prayer; record under module 'prayer'. */
import { getGrowWorld } from '../../api'
import { useLessonWorld } from './useLessonWorld'
import { keyOfPhrase, phrasesOf, prayerCards } from './prayerLesson'

export async function load() {
  const phrases = phrasesOf(await getGrowWorld('prayer'))
  return { order: phrases, all: phrases }
}

export function usePrayerWorld(world) {
  return useLessonWorld({ world, load, keyOf: keyOfPhrase, cards: prayerCards })
}
