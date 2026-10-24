/** The Prayer world: the words said in salah, from /api/grow/worlds/prayer; record under module 'prayer'. */
import { getGrowWorld } from '../../api'
import { useLessonWorld } from './useLessonWorld'
import { MODULE, keyOfPhrase, phrasesOf, prayerCards } from './prayerLesson'

async function load() {
  const phrases = phrasesOf(await getGrowWorld('prayer'))
  return { order: phrases, all: phrases }
}

export function usePrayerWorld(world) {
  return useLessonWorld({ world, module: MODULE, load, keyOf: keyOfPhrase, cards: prayerCards })
}
