/**
 * A topic's words as practice: the one place a word list becomes questions.
 *   wordDrills       every word once, for Quiz mode (hosted by Practice and ExerciseHost)
 *   reviewOf         which words are due, from the progress store's words summary
 *   reviewQuestions  the due words as Quiz-board questions, for Review
 * Both pick their wrong options with lib/quiz's buildQuestion, so the Quiz tab's
 * rules hold here too: a word of the same group first, never a synonym of the answer.
 * Every answer is filed under the word (WORDS_MODULE, wordKey), so the schedule
 * learns the word whichever mode or topic asked it. Pure and seeded: the same
 * words always make the same questions, and a rerender reshuffles nothing.
 */
import { buildQuestion, makeRandom } from './quiz'
import { QUIZ } from './quizBanks'

export const WORDS_MODULE = 'words'
export const wordKey = (dialect, word) => `${dialect}:${word.arabic}`

// A word listed twice in a topic is one word to the schedule, so it is asked once.
const once = (words, dialect) => [...new Map(words.map((w) => [wordKey(dialect, w), w])).values()]

const asQuiz = (w, dialect) => ({ ar: w.arabic, en: w.english, meaningKey: wordKey(dialect, w), groups: w.category ? [w.category] : [] })
const bankOf = (words, dialect) => once(words, dialect).map((w) => asQuiz(w, dialect))

// One Quiz-shaped question about `w`, its wrong options drawn from `bank`.
const questionOf = (w, i, direction, bank, dialect) =>
  buildQuestion([asQuiz(w, dialect)], { direction, optionCount: QUIZ.optionCount, distractorBank: bank, random: makeRandom(i + 1) })

/**
 * Quiz mode: one drill per word, as an ordinary exercise the registry draws, the
 * kinds taking turns, easiest first:
 *   pick    see the English, pick the Arabic
 *   listen  hear the Arabic, pick it
 *   write   see the English, write the Arabic (or how it sounds)
 * A topic of one word can only be written: there is nothing to pick it from.
 */
const DRILLS = ['pick', 'listen', 'write']

export function wordDrills(words, prefix, { dialect } = {}) {
  const bank = bankOf(words, dialect)
  return words.map((w, i) => {
    const kind = bank.length < 2 ? 'write' : DRILLS[i % DRILLS.length]
    const base = { id: `${prefix}.word.${i + 1}.${kind}`, answer: w.arabic, ...(dialect && { progress: { module: WORDS_MODULE, item: wordKey(dialect, w) } }) }
    if (kind === 'write') {
      return { ...base, type: 'translate_to_arabic', prompt: `Write “${w.english}” in Arabic, or how it sounds.`, accepted: [w.arabic, w.transliteration] }
    }
    const prompt = kind === 'pick' ? `Which one is “${w.english}”?` : 'Which word did you hear?'
    const options = questionOf(w, i, 'en-ar', bank, dialect).options.map((o) => o.text)
    return { ...base, type: 'choose', prompt, options, ...(kind === 'listen' && { say: w.arabic }) }
  })
}

/**
 * Review: a topic's words sorted by the schedule (FSRS, on the server, decides when
 * a word is due; this only sorts by it):
 *   due    answered before and due again now: the ones about to be forgotten
 *   fresh  never answered: next, so a topic is learnt as well as kept
 *   later  answered and not due yet: left alone, only counted
 */
export function reviewOf(words, rows, dialect) {
  const byItem = new Map(rows.map((r) => [r.item, r]))
  const due = [], fresh = [], later = []
  for (const w of once(words, dialect)) {
    const row = byItem.get(wordKey(dialect, w))
    if (!row) fresh.push(w)
    else (row.due ? due : later).push({ word: w, at: row.dueAt })
  }
  due.sort((a, b) => (a.at ?? '').localeCompare(b.at ?? ''))
  const next = later.map((l) => l.at).filter(Boolean).sort()[0] ?? null
  return {
    session: [...due.map((d) => d.word), ...fresh],
    due: due.length,
    fresh: fresh.length,
    later: later.length,
    next,
  }
}

// The kinds a review session takes turns over, one per word.
const REVIEWS = ['ar-en', 'en-ar', 'listen']

/**
 * One Quiz-board question per session word, answered by the word's progress key.
 * Wrong options come from the whole topic. A heard question is asked English to
 * Arabic, so its options are Arabic, then marked: the Arabic is spoken instead of
 * the English being shown, and the English prompt stays for the correction.
 */
export function reviewQuestions(session, words, dialect) {
  const bank = bankOf(words, dialect)
  return session.map((w, i) => {
    const kind = REVIEWS[i % REVIEWS.length]
    const question = questionOf(w, i, kind === 'listen' ? 'en-ar' : kind, bank, dialect)
    return kind === 'listen' ? { ...question, listen: true, say: w.arabic } : question
  })
}
