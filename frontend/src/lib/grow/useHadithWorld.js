/** The Hadith world: an-Nawawi's Forty (public/grow/nawawi40.json), record under module 'nawawi40'. */
import { fetchStatic } from '../api/staticQuery'
import { useLessonWorld } from './useLessonWorld'
import { SOURCE_URL, hadithCards, keyOfHadith } from './hadithLesson'

export async function load() {
  const { hadiths } = await fetchStatic(SOURCE_URL, 'the hadith')
  return { order: hadiths, all: hadiths }
}

export function useHadithWorld(world) {
  return useLessonWorld({ world, load, keyOf: keyOfHadith, cards: hadithCards })
}
