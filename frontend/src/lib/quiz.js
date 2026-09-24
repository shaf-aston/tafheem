/**
 * Question generation for the vocabulary quiz.
 *
 * Questions are built at run time from the word bank, never written down, so
 * the same bank keeps producing fresh combinations.
 *
 * Two rules keep a question fair, and they pull in opposite directions:
 *
 *   Plausible, a wrong option should be dismissable only by knowing the word.
 *   The same type of word is a rule, not a preference: "argued" offered as the
 *   meaning of a noun is dismissed without reading the Arabic, so a question
 *   that mixes types has already given itself away. Within one type, the
 *   answer's own topic comes first, then the options closest in length to the
 *   answer's own text, a one-word answer boxed in beside a whole clause gives
 *   itself away just as cheaply.
 *
 *   Unambiguous, exactly one option can be defended as correct. Every entry
 *   carries a `meaningKey`, and no two options in a question may share one. Since
 *   synonyms share a meaningKey, a synonym of the answer can never appear beside it.
 *
 * Pure functions throughout: pass in a random source and the output is
 * reproducible, which is what makes the rules testable.
 */

import { shuffled } from './shuffle'
import settings from '../quiz.json'

/**
 * The languages a meaning can be shown in, and the one thing about each that the
 * question builder has to know.
 *
 * `tail` is where a gloss keeps its grammar. English puts it first, "to carry
 * out" beside "to guide", so an option that opens the same way is the hard one.
 * Urdu puts it last, "اللہ کے", "جو رب ہے", so there it is the closing word that
 * has to match. Getting this backwards does not break a question, it just makes
 * every wrong option easy, which is worse because nothing looks wrong.
 *
 * Arabic is not in here: it is the word being learned, never the meaning shown.
 *
 * Two names on purpose. `label` is what the language calls itself and belongs on
 * a control, where a reader is looking for their own language. `name` is what an
 * English sentence calls it, because "a اردو meaning" reads badly and reorders
 * itself the moment a right-to-left word lands mid-sentence.
 */
export const MEANINGS = {
  en: { label: 'English', name: 'English', short: 'EN', tail: false },
  ur: { label: 'اردو', name: 'Urdu', short: 'UR', tail: true },
}

/**
 * Both ways round for every meaning language, derived rather than written out,
 * so a language can never arrive with only one of its two directions.
 */
export const DIRECTIONS = Object.fromEntries(
  Object.entries(MEANINGS).flatMap(([key, meaning]) => [
    [`ar-${key}`, {
      promptKey: 'ar', answerKey: key, promptLang: 'ar', answerLang: key,
      label: `Arabic → ${meaning.name}`, short: `AR → ${meaning.short}`,
    }],
    [`${key}-ar`, {
      promptKey: key, answerKey: 'ar', promptLang: key, answerLang: 'ar',
      label: `${meaning.name} → Arabic`, short: `${meaning.short} → AR`,
    }],
  ]),
)

// The count the panel passes is the one that reaches the screen; this is only
// what buildQuestion falls back to when a caller does not say. Read from the
// same setting the panel passes, so the two can never disagree.
const DEFAULT_OPTION_COUNT = settings['option-count']

// How many words to try before settling for the fullest question found. In any
// ordinary cut the first one works; this only bites where a word's type has
// almost no company, and it stops a thin cut from being searched end to end.
const ATTEMPTS = 12

/** Small seedable generator, a seed makes a run repeatable for tests. */
export function makeRandom(seed = 1) {
  let state = seed >>> 0
  return () => {
    state = (state + 0x6d2b79f5) >>> 0
    let t = Math.imul(state ^ (state >>> 15), 1 | state)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const wordCount = (text) => text.trim().split(/\s+/).length

/**
 * Wrong options for one answer: never a different type of word, never two that
 * mean the same thing, and within that, trickiest first.
 *
 * May return fewer than `count`. A bank that cannot supply enough words of the
 * answer's own type asks a shorter question instead of padding it with one that
 * answers itself, 26 of the 114 surah word lists are that thin for at least one
 * type, so this is the normal case there, not an edge case.
 *
 * `answerKey` is which field will actually be shown as the option text, `en`
 * translations range from one word to a whole clause, so sorting by length
 * only makes sense against the field the player will actually see.
 */
export function pickDistractors(bank, answer, count, random, answerKey = 'en') {
  const answerLength = wordCount(answer[answerKey])

  // Undefined fields never match: two words the corpus never tagged are not
  // alike just because both are blank.
  const matches = (word, field) => word[field] != null && word[field] === answer[field]

  // The hard rule. Every word the build ships says what type it is; the one
  // exception is a word whose own list could not settle it, which is still
  // asked and falls back to the topic below rather than being dropped.
  //
  // Then: a word with nothing written in the language being shown cannot be an
  // option, it would put a blank button on screen. Only the Qur'anic words have
  // an Urdu meaning, so in an Urdu round this is what keeps the rest out.
  const eligible = (answer.wordType != null ? bank.filter((word) => matches(word, 'wordType')) : bank)
    .filter((word) => word[answerKey])

  // Within one type, how hard a word is to dismiss without reading the question.
  //
  // First, whether it is shaped the same way. Two sources gloss a verb
  // differently, "to carry out" from a dictionary, "He guides" from a
  // word-by-word Qur'an, and an option in the other shape is spotted without
  // reading the Arabic, however long it is. Matching that is what lets a full
  // dictionary meaning sit in a question safely: beside three other "to …"
  // options, its length stops being the tell.
  //
  // Which end carries the shape is the language's own business, so MEANINGS
  // says it. Only worth doing on the meaning side: the Arabic options are single
  // words, so they have no end to share and every one would score the same.
  //
  // Then a topic it shares with the answer, then whichever is closest in
  // length. A word can sit in more than one group, a book verb is both a baab
  // and a topic, so one shared group is enough.
  const shownIn = MEANINGS[answerKey]
  const edgeWord = (text) => {
    const parts = (text ?? '').trim().toLowerCase().split(/\s+/)
    return shownIn?.tail ? parts[parts.length - 1] : parts[0]
  }
  const answerEdge = shownIn ? edgeWord(answer[answerKey]) : null
  const sameShape = (word) => (
    answerEdge != null && edgeWord(word[answerKey]) === answerEdge ? 1 : 0
  )

  const shared = new Set(answer.groups ?? [])
  const affinity = (word) => ((word.groups ?? []).some((group) => shared.has(group)) ? 1 : 0)
  const byPlausibility = (a, b) => (
    sameShape(b) - sameShape(a)
    || affinity(b) - affinity(a)
    || Math.abs(wordCount(a[answerKey]) - answerLength) - Math.abs(wordCount(b[answerKey]) - answerLength)
  )

  const candidates = shuffled(
    eligible.filter((word) => word.meaningKey !== answer.meaningKey), // a synonym is never a wrong answer
    random,
  ).sort(byPlausibility)

  const chosen = []
  const usedMeanings = new Set([answer.meaningKey])

  for (const candidate of candidates) {
    if (chosen.length === count) break
    if (usedMeanings.has(candidate.meaningKey)) continue // options stay distinct from each other
    usedMeanings.add(candidate.meaningKey)
    chosen.push(candidate)
  }

  return chosen
}

/**
 * One question. `exclude` holds the meanings already asked this round, so a
 * session works through the bank instead of circling the same few words.
 */
export function buildQuestion(bank, {
  direction = 'ar-en',
  optionCount = DEFAULT_OPTION_COUNT,
  exclude = new Set(),
  random = Math.random,
  distractorBank = null,
} = {}) {
  const shape = DIRECTIONS[direction]
  if (!shape) throw new Error(`Unknown quiz direction: ${direction}`)

  // Which words may be asked and which may stand beside them are two different
  // questions, and only the mistakes round has to separate them: there the
  // words to ask are the handful got wrong, while the wrong options should
  // still come from everything. Kept apart, one mistake is a fair question on
  // the day it is made. Fused, as every other round has them, a learner with
  // three mistakes of three different types could never be asked at all, which
  // is exactly when review is worth the most.
  const optionsFrom = distractorBank ?? bank

  if (!bank.length) throw new Error('The quiz bank is empty.')

  // A word can only be asked in a language it is written in. Only the Qur'anic
  // words carry an Urdu meaning, so an Urdu round over the everyday set has
  // nothing to ask; that is a real answer and it says so rather than putting
  // empty buttons on the screen.
  const askable = bank.filter((w) => w[shape.promptKey] && w[shape.answerKey])
  if (!askable.length) throw new Error(`No word in the quiz bank is written in ${shape.answerLang}.`)

  const unasked = askable.filter((w) => !exclude.has(w.meaningKey))
  const pool = unasked.length ? unasked : askable // bank exhausted, start over

  // Ask a word this cut can ask fairly. Since wrong options must be the same
  // type as the answer, a word whose type has almost no company here; the one
  // adjective in a group of nouns, cannot fill a question, and asking it would
  // put a single option on screen. Try the next word instead; it can still be
  // asked from a wider cut. The best attempt is kept, so a genuinely thin cut
  // still asks its shorter question rather than none.
  let answer = null
  let distractors = []
  for (const candidate of shuffled(pool, random).slice(0, ATTEMPTS)) {
    const found = pickDistractors(optionsFrom, candidate, optionCount - 1, random, shape.answerKey)
    if (answer === null || found.length > distractors.length) {
      answer = candidate
      distractors = found
    }
    if (distractors.length === optionCount - 1) break
  }
  const options = shuffled([answer, ...distractors], random).map((word) => ({
    id: word.meaningKey,
    text: word[shape.answerKey],
  }))

  return {
    direction,
    prompt: answer[shape.promptKey],
    promptLang: shape.promptLang,
    answerLang: shape.answerLang,
    answerId: answer.meaningKey,
    answerText: answer[shape.answerKey],
    // Set when this word never stands alone in the Qur'an, so its English is
    // borrowed from a place it was attached to another word. Carried through to
    // the question rather than dropped, so the panel can say so.
    attached: Boolean(answer.attached),
    // What these letters mean to someone who reads Urdu, where a person has
    // checked. Null on nearly every word, which is the honest state: see
    // backend/scripts/build_urdu_links.py.
    urdu: answer.urdu ?? null,
    options,
  }
}
