/**
 * Reading "Nisa 45" as a place: surah An-Nisa, ayah 45.
 *
 * Pure: text in, matches out. The Quran tab's box and the header command bar
 * both ask this, so they can never disagree about what a typed name means.
 *
 * A name is matched the way a person types it, not the way the mushaf prints
 * it: no "an-", no apostrophes, doubled vowels collapsed ("Nisaa"), i and e
 * treated alike ("Yaseen"). The number after a name is always the ayah, and a
 * lone number is a surah. Matches are ranked exact, then prefix, then anywhere
 * in the name, then one or two typos away, so callers can choose how loose to be.
 */
import surahs from '../data/surahs.json'
import { bareForm, isArabic } from './arabicText'

/** How close a match is. Lower is closer; callers pick the loosest they accept. */
export const CLOSE = { exact: 0, prefix: 1, inside: 2, typo: 3 }

const FILLER = /\b(surah|surat|sura|chapter|ayah|ayat|aya|verse|v|no|number)\b\.?/g
const ARABIC_DIGITS = '٠١٢٣٤٥٦٧٨٩'
const LATIN_ARTICLE = /^(?:al|an|ar|as|at|ad|adh|ash|ath|az|ali)[-\s]/i
const ARABIC_ARTICLE = /^ال/

const digitsToLatin = (text) => text.replace(/[٠-٩]/g, (d) => ARABIC_DIGITS.indexOf(d))

/** Letters only, doubles collapsed, e/o folded to i/u: how a name sounds. */
const foldLatin = (text) =>
  text.toLowerCase().replace(/[^a-z]/g, '').replace(/(.)\1+/g, '$1').replace(/e/g, 'i').replace(/o/g, 'u')

const foldArabic = (text) => bareForm(text).replace(/[^؀-ۿ]/g, '')

/** Every spelling one surah answers to: with and without its article. */
const keys = surahs.map((s) => {
  const en = [foldLatin(s.en), foldLatin(s.en.replace(LATIN_ARTICLE, ''))]
  const ar = foldArabic(s.ar)
  return { s, latin: en, arabic: [ar, ar.replace(ARABIC_ARTICLE, '')] }
})

function editDistance(a, b) {
  const row = Array.from({ length: b.length + 1 }, (_, i) => i)
  for (let i = 1; i <= a.length; i++) {
    let diag = row[0]
    row[0] = i
    for (let j = 1; j <= b.length; j++) {
      const up = row[j]
      row[j] = Math.min(row[j] + 1, row[j - 1] + 1, diag + (a[i - 1] === b[j - 1] ? 0 : 1))
      diag = up
    }
  }
  return row[b.length]
}

/** How many typos a name of this length may have and still be recognised. */
const allowedTypos = (length) => (length <= 4 ? 0 : length <= 7 ? 1 : 2)

function closeness(needle, spellings) {
  let best = Infinity
  for (const spelling of spellings) {
    if (!spelling) continue
    let score = Infinity
    if (spelling === needle) score = CLOSE.exact
    else if (needle.length >= 2 && spelling.startsWith(needle)) score = CLOSE.prefix
    else if (needle.length >= 3 && spelling.includes(needle)) score = CLOSE.inside
    else if (editDistance(needle, spelling) <= allowedTypos(needle.length)) score = CLOSE.typo
    best = Math.min(best, score)
  }
  return best
}

/** Surahs a typed name could mean, closest first, at most `limit`. */
export function surahsNamed(name, limit = 5) {
  const arabic = isArabic(name)
  const needle = arabic ? foldArabic(name).replace(ARABIC_ARTICLE, '') : foldLatin(name)
  if (!needle) return []
  return keys
    .map(({ s, latin, arabic: ar }) => ({ ...s, close: closeness(needle, arabic ? ar : latin) }))
    .filter((m) => m.close < Infinity)
    .sort((a, b) => a.close - b.close || a.n - b.n)
    .slice(0, limit)
}

/**
 * What a typed line names. `ayah` is null when only a surah was given.
 * `matches` is empty when nothing was recognised.
 */
export function readSurahRef(text) {
  const line = digitsToLatin(text ?? '').toLowerCase().replace(FILLER, ' ').trim()
  if (!line) return { matches: [], ayah: null }

  const bare = /^(\d{1,3})(?:\s*[:.,،٬\s-]\s*(\d{1,3}))?$/.exec(line)
  if (bare) {
    const surah = surahs[Number(bare[1]) - 1]
    const ayah = bare[2] ? Number(bare[2]) : null
    return { matches: surah ? [{ ...surah, close: CLOSE.exact }] : [], ayah }
  }

  const numbers = line.match(/\d{1,3}/g)
  const ayah = numbers ? Number(numbers[numbers.length - 1]) : null
  return { matches: surahsNamed(line.replace(/[\d:.,،٬-]+/g, ' ')), ayah }
}

/** Why an ayah number cannot be opened in this surah, or null when it can. */
export function ayahProblem(surah, ayah) {
  if (ayah === null) return null
  if (ayah < 1) return 'Ayahs start at 1'
  if (ayah > surah.ayahs) return `${surah.en} has ${surah.ayahs} ayahs`
  return null
}
