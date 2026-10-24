/**
 * Quran world cards for a few short surahs (config: worlds.json `surahs`), record under module 'quran-ayat'.
 * Per ayah: a teach card, then "complete it" (lib/quiz/gap.js). The text is the server's /quran/surah, as shown in the reader.
 */
import { getQuranSurah } from '../../api'
import { gapOf } from '../quiz/gap'
import { weave } from './lesson'

export const MODULE = 'quran-ayat'
export const keyOfAyah = (ayah) => `${ayah.surah}:${ayah.ayah}`

/** The ayahs of `surahs`, flat, in the given order. */
export async function loadSurahs(surahs) {
  const loaded = await Promise.all(surahs.map((surah) => getQuranSurah(surah)))
  return loaded.flatMap(({ surah, name_en, name_ar, ayahs }) =>
    ayahs.map(({ ayah, arabic, english }) => ({ surah, ayah, arabic, english, name_en, name_ar })))
}

/** `picked` from lessonItems; `all` every ayah of the world. A new ayah is taught then asked; a review is asked. */
export function quranCards(picked, all, random = Math.random) {
  const gap = (ayah, tag) => {
    const key = keyOfAyah(ayah)
    const blank = gapOf(ayah.arabic, all.filter((other) => other !== ayah).map((other) => other.arabic), random)
    return {
      kind: 'gap', id: `gap:${key}`, tag, gap: blank, answerText: blank.answer,
      record: { module: MODULE, item: key, context: { world: 'quran', ask: 'gap' } },
    }
  }
  return weave(picked, {
    teach: (ayah) => ({ kind: 'ayah', id: `teach:${keyOfAyah(ayah)}`, tag: 'New ayah', ayah }),
    asks: (ayah, isNew) => [gap(ayah, isNew ? 'New ayah' : 'Review')],
  })
}
