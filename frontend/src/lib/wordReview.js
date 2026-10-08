/**
 * Which of a topic's words to review now, from the progress store's summary of
 * the words module. The schedule itself (FSRS, on the server) decides when a word
 * is due; this only sorts a topic's words by it:
 *   due    answered before and due again now: the ones about to be forgotten
 *   fresh  never answered: next, so a topic is learnt as well as kept
 *   later  answered and not due yet: left alone, only counted
 * Pure, so the order is testable without a server.
 */
import { buildQuestion, makeRandom } from './quiz'
import { QUIZ } from './quizBanks'
import { wordKey } from './wordDrills'

// A word listed twice in a topic is one word to the schedule, so it is asked once.
const once = (words, dialect) => [...new Map(words.map((w) => [wordKey(dialect, w), w])).values()]

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

// The kinds of question a session takes turns over, one per word.
const KINDS = ['ar-en', 'en-ar', 'listen']

/**
 * One Quiz-shaped question per session word, answered by the word's progress
 * key. Wrong options come from the whole topic. A heard question is asked in
 * English-to-Arabic, so its options are Arabic, then marked: the Arabic is
 * spoken instead of the English being shown, and the English prompt stays for
 * the correction after the answer.
 */
export function reviewQuestions(session, words, dialect) {
  const asQuiz = (w) => ({ ar: w.arabic, en: w.english, meaningKey: wordKey(dialect, w) })
  const distractorBank = once(words, dialect).map(asQuiz)
  return session.map((w, i) => {
    const kind = KINDS[i % KINDS.length]
    const question = buildQuestion([asQuiz(w)], {
      direction: kind === 'listen' ? 'en-ar' : kind,
      optionCount: QUIZ.optionCount,
      distractorBank,
      random: makeRandom(i + 1),
    })
    return kind === 'listen' ? { ...question, listen: true, say: w.arabic } : question
  })
}
