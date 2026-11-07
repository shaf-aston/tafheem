/**
 * The ayah of the day on the Qur'an tab's opening page: one reference from
 * config/quran.json's short list, chosen by the local calendar date, so it is
 * the same all day and the next one tomorrow. The text is the backend's.
 */
import QURAN from '../../config/quran.json'
import { AYAH_REF } from './surahRef'

const DAY_MS = 86_400_000

// The local date counted in whole days. Its parts are read back through UTC,
// where every day is 24 hours, so a clock change never skips or repeats one.
const dayNumber = (date) => (Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) / DAY_MS)

export function todayAyah(date = new Date(), refs = QURAN.today) {
  const [, surah, ayah] = AYAH_REF.exec(refs[dayNumber(date) % refs.length])
  return { surah: Number(surah), ayah: Number(ayah) }
}
