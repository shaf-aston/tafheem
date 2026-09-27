/**
 * What a line typed into the Qur'an tab's one box is asking for: a place
 * (a surah, or a surah and an ayah) or the words of the mushaf.
 *
 * Pure, and the only place that decides it, so the box, its hint line and the
 * tests can never disagree. The reading of names and numbers is lib/surahRef's;
 * this only decides which of the two questions the line is.
 *
 * The boundary leans towards the words. A wrong guess of "place" throws the
 * reader's text away for an ayah they did not ask for, while a wrong guess of
 * "words" still lists matches, and a surah whose name was typed exactly is
 * offered beside them. So a line is a place only when it could not be text:
 *   - numbers alone ("2:255", "18", "٢:٢٥٥")
 *   - Latin letters, since the mushaf is only searched in Arabic ("Nisa 45")
 *   - Arabic with a number or a leading سورة, closely matching a surah name
 *     ("النساء ٤٥", "سورة الكهف")
 * Diacritics always mean a quote: nobody vowels a surah's name to find it.
 */
import { hasDiacritics, isArabic } from './arabicText'
import { CLOSE, ayahProblem, readSurahRef, surahsNamed } from './surahRef'

/** The kinds of question; `none` is an empty box. */
export const KIND = { none: 'none', ayah: 'ayah', surah: 'surah', text: 'text' }

const NUMBERS_ONLY = /^[\d٠-٩\s:.,،٬-]+$/
const SURAH_WORD = /^\s*سور[ةه]\s*/
const HAS_NUMBER = /[\d٠-٩]/

const place = (matches, ayah) => ({
  kind: ayah === null ? KIND.surah : KIND.ayah,
  surahs: matches,
  ayah,
  problem: ayahProblem(matches[0], ayah),
})

/**
 * `{ kind, surahs, ayah, problem }`. For a place, `surahs[0]` is the one Enter
 * opens and the rest are near misses to pick from. For text, `surahs` holds a
 * surah whose name is exactly what was typed, offered on the side, never opened
 * by Enter. `problem` is set when Enter can do nothing and says why.
 */
export function readQuranQuery(text) {
  const line = (text ?? '').trim()
  if (!line) return { kind: KIND.none, surahs: [], ayah: null, problem: null }

  if (NUMBERS_ONLY.test(line) && HAS_NUMBER.test(line)) {
    const { matches, ayah } = readSurahRef(line)
    if (matches.length === 0) {
      return { kind: KIND.ayah, surahs: [], ayah, problem: 'There are 114 surahs. Try 2:255, or a surah’s name.' }
    }
    return place(matches, ayah)
  }

  if (hasDiacritics(line)) return wordsOf(line)

  if (!isArabic(line)) {
    const { matches, ayah } = readSurahRef(line)
    if (matches.length === 0) {
      return {
        kind: KIND.surah, surahs: [], ayah,
        problem: 'No surah by that name. To search the words, type them in Arabic.',
      }
    }
    return place(matches, ayah)
  }

  if (SURAH_WORD.test(line) || HAS_NUMBER.test(line)) {
    const { matches, ayah } = readSurahRef(line.replace(SURAH_WORD, ''))
    const close = matches.filter((m) => m.close < CLOSE.typo)
    if (close.length) return place(close, ayah)
  }

  return wordsOf(line)
}

// Words, with a surah offered on the side only when its name is exactly what
// was typed: "الرحمن" is a word of the mushaf and the name of surah 55.
function wordsOf(line) {
  const named = isArabic(line) ? surahsNamed(line, 1).filter((m) => m.close === CLOSE.exact) : []
  return { kind: KIND.text, surahs: named, ayah: null, problem: null }
}
