/**
 * Where the Similar verses tab is: "2:3", the verse whose pairs are open, the
 * same "surah:ayah" the Quran tab uses, so /app/similar/2:3 and the reader's
 * "look-alikes" link say the same thing. Pure: a verse that has no pair is left
 * to the panel, which then opens the surah's first.
 */
import { AYAH_REF, isAyah } from '../quran/surahRef'

/** { surah, ayah } for "2:3", null for anything else or an ayah that does not exist. */
export function parsePlace(q) {
  const found = AYAH_REF.exec(q ?? '')
  if (!found) return null
  const place = { surah: Number(found[1]), ayah: Number(found[2]) }
  return isAyah(place) ? place : null
}

export const placeOf = (key) => key
