/** The Quran world: the short surahs of worlds.json `surahs` (from /quran/surah), record under module 'quran-ayat'. */
import { useLessonWorld } from '../grow/useLessonWorld'
import { keyOfAyah, loadSurahs, quranCards } from '../grow/quranLesson'

export function useQuranWorld(world) {
  const load = async () => {
    const ayahs = await loadSurahs(world.surahs)
    return { order: ayahs, all: ayahs }
  }
  return useLessonWorld({ world, load, keyOf: keyOfAyah, cards: quranCards })
}
