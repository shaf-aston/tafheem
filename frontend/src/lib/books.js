/**
 * The books Memorise can work from.
 *
 * One entry per book, and a book only has to answer two questions: what parts
 * are there to choose from, and what are the lines of one part. Both are asked
 * for rather than listed, because a book's own parts can live inside its text:
 * the Qur'an's surahs are known before anything is read, but a poem's baabs are
 * headings inside the poem itself. Every book answers the same way, parts()
 * gives {id, label}, and load(id) gives that part's lines. Everything
 * above this file, paging, blanking, marking; works on lines and never learns
 * which book they came from, so a second book is a second entry here rather
 * than a second panel.
 *
 * A line is the unit the book itself breaks on: an ayah for the Qur'an, and
 * whatever the next book breaks on for that one. It is never split further,
 * because half of one is not something anyone memorises.
 */

import { getQuranSurah } from '../api'
import { PAGE_WORDS, wordsOf } from './memorise'

/** 114 surahs, numbered. Their names arrive with the text, so none are held here. */
const SURAHS = Array.from({ length: 114 }, (_, i) => ({ id: i + 1, label: String(i + 1) }))

/**
 * The poem, fetched at most once however many times it is asked for; its
 * baabs and its verses are two questions about one small file, not two files.
 */
let poemOnce = null
const poem = () => {
  poemOnce ??= fetch('/jazariyya/poem.json').then((res) => {
    if (!res.ok) throw new Error('Could not read the Jazariyyah text')
    return res.json()
  })
  return poemOnce
}

/**
 * The poem's baabs, each with the verses it runs over. A section marks the
 * bayt it starts after, so it holds everything from the next one up to wherever
 * the following section starts, and the last one runs to the end.
 */
const baabsOf = (p) => p.sections.map((section, i) => ({
  id: i + 1,
  label: section.title,
  from: section.afterBaytN + 1,
  to: p.sections[i + 1]?.afterBaytN ?? p.totalBayt,
}))

export const BOOKS = {
  quran: {
    id: 'quran',
    label: "Qur'an",
    arabic: 'القرآن',
    /** What the reader picks from, and what one of them is called. */
    partLabel: 'Surah',
    parts: async () => SURAHS,
    // Only used if the Madani layout has never been built. When it has, each
    // ayah arrives knowing its printed page and pagesOf groups by that instead.
    wordsPerPage: PAGE_WORDS,
    // Off to start with, naming the missing word gives it away for free, and
    // is only wanted when stuck, not while trying.
    meaningDefault: false,
    // Each line is an ayah whose label the backend can check words against by
    // sound, so the checking level applies. The poem has no such text.
    checkedBySound: true,
    /**
     * One part as lines, plus whatever the book wants to show as its title.
     * The same endpoint the Quran tab reads, the text is not fetched twice
     * and not stored twice.
     */
    load: async (part) => {
      const surah = await getQuranSurah(part)
      return {
        title: `${surah.surah}. ${surah.name_en}`,
        arabicTitle: surah.name_ar,
        lines: surah.ayahs.map((ayah) => ({
          id: ayah.ayah,
          label: `${surah.surah}:${ayah.ayah}`,
          arabic: ayah.arabic,
          english: ayah.english,
          // The page of the Madani mushaf this ayah begins on, when the layout
          // has been built, pagesOf groups by it and the estimate steps aside.
          page: ayah.page,
        })),
      }
    },
  },
  jazariyya: {
    id: 'jazariyya',
    label: 'Al-Jazariyyah',
    arabic: 'المقدمة الجزرية',
    // The poem's own chapter headings. A hundred and seven verses in one list
    // is not something anyone sits down to memorise; a baab is.
    partLabel: 'Baab',
    parts: async () => baabsOf(await poem()).map(({ id, label }) => ({ id, label })),
    // A bayt is about ten words and prints as two half-lines, so a mushaf-sized
    // page of 15 printed lines is around seven or eight of them, not the 13
    // that counting words alone would pack in.
    wordsPerPage: 75,
    // On to start with. Each gloss describes the verse rather than handing
    // back its missing word, and this text has no other way in for a learner
    // without a teacher, unlike the Qur'an most readers already know by ear.
    meaningDefault: true,
    /**
     * A static file fetched once, the same pattern as public/words/; a small,
     * fixed text with one reader does not need a backend or a database.
     * See public/jazariyya/README.md for where the Arabic and English come from.
     */
    load: async (part) => {
      const text = await poem()
      const baab = baabsOf(text).find((b) => b.id === part)
      if (!baab) throw new Error('There is no such baab in this poem')
      return {
        title: baab.label,
        arabicTitle: text.arabicTitle,
        lines: text.bayt.filter((b) => b.n >= baab.from && b.n <= baab.to).map((b) => ({
          id: b.n,
          label: String(b.n),
          arabic: `${b.sadr} ${b.ajuz}`,
          english: b.english,
          // Where the sadr ends and the ajuz begins, so the line can be shown
          // as the two hemistichs of a bayt rather than one run-on sentence, 
          // a word count, not a second fetch or a second field to keep in sync.
          breakAfter: wordsOf(b.sadr).length - 1,
        })),
      }
    },
  },
}

export const DEFAULT_BOOK = 'quran'
