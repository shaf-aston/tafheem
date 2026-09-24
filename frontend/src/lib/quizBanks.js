/**
 * The quiz's config seam: the words, and every setting the panel reads.
 *
 * Two other files read one number out of quiz.json for themselves, the count
 * of options a question offers: the question builder beside this one, as the
 * fallback for a caller that does not say, and Memorise, whose gaps offer the
 * same number of words. One number, one place, three readers.
 *
 * Every word the quiz can ask about lives in one table, built by
 * backend/scripts/build_lexicon.py and shipped as three files under
 * public/words/: every word once in words.json, and cuts.json saying which
 * words are in each cut, as positions into that array.
 *
 * So a cut is a list of numbers, not a list of words. Picking a surah, a juz, a
 * topic or a whole set is the same operation on the same array, nothing is
 * fetched a second time, nothing is merged, and no word is held twice.
 *
 * A group narrows a round down. Narrowing also narrows where the wrong options
 * come from, which makes a round harder on purpose: every option is then from
 * the same topic, the same verb pattern, or the same surah.
 */
import settings from '../quiz.json'
import { fetchReviewItems } from './progress'

export const QUIZ = {
  optionCount: settings['option-count'],
  direction: settings['default-direction'],
  language: settings['meaning-language'],
  bank: settings['default-bank'],
  autoNext: settings['auto-next'],
  autoNextMs: settings['auto-next-ms'],
  autoNextWrongMs: settings['auto-next-wrong-ms'],
  insightMinAttempts: settings['insight-min-attempts'],
}

/** Which panel the progress store files this tab's answers under. */
export const MODULE = 'quiz'

/**
 * ...and which one when the meanings are shown in another language.
 *
 * Knowing that كِتاب means "book" and knowing it means "کتاب" are two things a
 * reader learns separately, so they are counted separately: an Urdu round never
 * moves an English score, and Mistakes offers back the words got wrong in the
 * language they were asked in. The store files under whatever name it is given
 * and cares about nothing else, so this costs one name.
 *
 * English keeps the bare name it has always had, so every answer already saved
 * still counts.
 */
export const moduleFor = (language) => (language === 'en' ? MODULE : `${MODULE}:${language}`)

const WORDS_DIR = '/words'

/**
 * The three sets on the first control, and which cut each one is. `all` has no
 * cut: it is every word there is, which is now simply no filter rather than
 * three lists stitched together with the overlaps removed.
 */
export const BANKS = {
  quranic: { label: "Qur'anic", cut: 'book', grouped: true },
  everyday: { label: 'Everyday', cut: 'everyday', grouped: false },
  all: { label: 'All', cut: null, grouped: false },
  // The only set that is not a cut of the table. Its words are whichever ones
  // have been got wrong and not yet got right twice, which the progress store
  // decides and this module only asks for. `live` marks that: a cut is the same
  // every time it is read, this changes as the learner answers.
  mistakes: { label: 'Mistakes', cut: null, grouped: false, live: true },
}

/**
 * The first control's two whole-set choices, no second picker follows them,
 * unlike Topic, Surah and Juz which each need one.
 */
export const WHOLE_SET_SCOPES = [
  // Named for what it is: the book's own 385-word list, not every word in the
  // Qur'an, that one is the entry below it.
  { id: 'all', label: '80% book', group: '' },
  { id: 'quran', label: 'Whole Qur’an', group: 'quran:all' },
]

async function fetchJson(path) {
  const response = await fetch(path)
  if (!response.ok) throw new Error(`Could not load ${path} (${response.status})`)
  return response.json()
}

/** The three files, fetched once between them and then remembered. */
let loading = null
function load() {
  loading ??= Promise.all([
    fetchJson(`${WORDS_DIR}/words.json`),
    fetchJson(`${WORDS_DIR}/cuts.json`),
    fetchJson(`${WORDS_DIR}/index.json`),
  ]).then(([words, cuts, index]) => ({ words: words.words, cuts, index }))
  return loading
}

/** Which cut a bank and a group id name between them. */
const cutFor = (bankId, groupId) => {
  const bank = BANKS[bankId]
  if (!bank) throw new Error(`Unknown quiz bank: ${bankId}`)
  if (!groupId) return bank.cut
  // The whole-Qur'an scope is a set, not a group inside one.
  return groupId === 'quran:all' ? 'quran' : groupId
}

/** Every word there is, which the mistakes round draws its wrong options from. */
export async function allWords() {
  return (await load()).words
}

/**
 * The words to quiz on: a whole set, one group inside it, or the mistakes.
 *
 * `language` only matters to Mistakes, which has to ask the store for the pile
 * owed in the language being asked; every other set is the same words whichever
 * language they are shown in, and buildQuestion drops the ones with nothing
 * written in it.
 */
export async function wordsFor(bankId, groupId = '', language = QUIZ.language) {
  const { words, cuts } = await load()

  // Asked for by id, then found in the table the page already holds. A word got
  // wrong long enough ago that it has since left the word list simply does not
  // come back, which is the honest answer: it cannot be asked any more.
  if (BANKS[bankId]?.live) {
    const owed = new Set(await fetchReviewItems(moduleFor(language)))
    return words.filter((word) => owed.has(word.meaningKey))
  }

  const cut = cutFor(bankId, groupId)
  if (cut === null) return words // "All", every word, no filter

  const positions = cuts[cut]
  if (!positions) throw new Error(`Unknown quiz group: ${groupId}`)
  return positions.map((at) => words[at])
}

/**
 * What to say about a set beside the question, the dialect its words are in,
 * and where they came from. Read from the table's own record of each list
 * rather than repeated here.
 */
export async function bankInfo(bankId) {
  const { index } = await load()
  return index.sets.find((set) => set.id === BANKS[bankId]?.cut) ?? {}
}

/**
 * Everything the group picker offers for a bank, in labelled sections so the
 * book's topics never sit in an undivided list beside 114 surahs.
 *
 * `size` is how many words the group holds; the picker uses it to grey out a
 * short surah that cannot fill a question.
 */
export async function groupsFor(bankId) {
  if (!BANKS[bankId]?.grouped) return []

  const { cuts, index } = await load()
  const book = index.sets.find((set) => set.id === 'book')

  return [
    {
      id: 'book',
      label: 'Topic',
      hint: 'The 385-word list, grouped the way the book groups it',
      options: book.groups.map((group) => ({
        id: `book:${group.id}`,
        label: group.label,
        size: cuts[`book:${group.id}`].length,
      })),
    },
    {
      id: 'surah',
      label: 'Surah',
      hint: 'Every word of one surah',
      options: index.surahs.map((s) => ({ id: `surah:${s.id}`, label: `${s.id}. ${s.name}`, size: s.words })),
    },
    {
      id: 'juz',
      label: 'Juz',
      hint: 'Every word of one juz',
      options: index.juz.map((j) => ({ id: `juz:${j.id}`, label: `Juz ${j.id}`, size: j.words })),
    },
  ]
}
