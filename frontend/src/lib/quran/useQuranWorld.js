/** The Quran world: the short surahs of worlds.json `surahs` (from /quran/surah), record under module 'quran-ayat'. */
import { useLessonWorld } from '../grow/useLessonWorld'
import { keyOfAyah, loadSurahs, quranCards } from '../grow/quranLesson'

export const loadQuran = (world) => async () => {
  const ayahs = await loadSurahs(world.surahs)
  return { order: ayahs, all: ayahs }
}

export function useQuranWorld(world) {
  return useLessonWorld({ world, load: loadQuran(world), keyOf: keyOfAyah, cards: quranCards })
}
