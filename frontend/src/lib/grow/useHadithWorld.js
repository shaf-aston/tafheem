/** The Hadith world: an-Nawawi's Forty (public/grow/nawawi40.json), record under module 'nawawi40'. */
import { useLessonWorld } from './useLessonWorld'
import { MODULE, SOURCE_URL, hadithCards, keyOfHadith } from './hadithLesson'

async function load() {
  const response = await fetch(SOURCE_URL)
  if (!response.ok) throw new Error(`Could not load the hadith (${response.status})`)
  const { hadiths } = await response.json()
  return { order: hadiths, all: hadiths }
}

export function useHadithWorld(world) {
  return useLessonWorld({ world, module: MODULE, load, keyOf: keyOfHadith, cards: hadithCards })
}
