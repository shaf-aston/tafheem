/**
 * The Qur'an's own words, as the export ships them (build_lexicon.py, then
 * export_quiz_words.py).
 *
 * This bank is the one nobody curated: 3,650 lemmas straight out of the corpus,
 * with no topics on them. So the two things that keep a question fair here are
 * both properties of the build, names are gone, and every word says which type
 * it is, and both are asserted against the file the app actually fetches.
 *
 * Surah 9 is the sample because it is where حُنَيْن sits, the name that used to
 * be offered as a meaning for قَلَم.
 */
import { describe, expect, it } from 'vitest'

import cuts from '../../public/words/cuts.json'
import words from '../../public/words/words.json'
import { DIRECTIONS, makeRandom, pickDistractors } from './quiz'

/** One cut, resolved the way the app resolves it: positions into one array. */
const cut = (name) => cuts[name].map((at) => words.words[at])

const WORDS = cut('surah:9')
const WORD_TYPES = ['noun', 'verb', 'adjective']

describe('the whole-Qur\'an word bank', () => {
  it('fills in every field the quiz reads', () => {
    for (const word of WORDS) {
      expect(word.ar, JSON.stringify(word)).toBeTruthy()
      expect(word.en, JSON.stringify(word)).toBeTruthy()
      expect(word.meaningKey, JSON.stringify(word)).toBeTruthy()
      expect(WORD_TYPES, JSON.stringify(word)).toContain(word.wordType)
    }
  })

  it('holds no names, a name is Islamic knowledge, not Arabic vocabulary', () => {
    const meanings = WORDS.map((w) => w.meaningKey)
    expect(meanings).not.toContain('hunain')
  })
})

// Asked of the words themselves rather than of a built question: this bank is
// copied from a book that lists real synonyms, so two entries can share a sense
// and an option's id cannot be traced back to one word.
describe.each(Object.keys(DIRECTIONS))('wrong options in the %s direction', (direction) => {
  const { answerKey } = DIRECTIONS[direction]

  it('are always the same kind of word as the answer', () => {
    for (let seed = 1; seed <= 120; seed++) {
      const answer = WORDS[seed * 37 % WORDS.length]
      const distractors = pickDistractors(WORDS, answer, 3, makeRandom(seed), answerKey)
      expect(distractors, answer.en).toHaveLength(3)
      for (const wrong of distractors) expect(wrong.wordType, `${answer.en} (${answer.wordType})`).toBe(answer.wordType)
    }
  })

  // Surah 9 is large enough that three of every kind are always there, which is
  // why a sort that merely *preferred* the same kind passed here for so long.
  // Al-Fil is one of the 26 surahs where that is not true, it holds two
  // adjectives in total, so this is where the rule has to actually hold.
  it('run short rather than borrow another kind, on a surah too thin to fill', () => {
    const thin = cut('surah:105')
    for (let seed = 1; seed <= 60; seed++) {
      const answer = thin[seed * 7 % thin.length]
      const distractors = pickDistractors(thin, answer, 3, makeRandom(seed), answerKey)
      expect(distractors.length, answer.en).toBeLessThanOrEqual(3)
      for (const wrong of distractors) {
        expect(wrong.wordType, `${answer.en} (${answer.wordType})`).toBe(answer.wordType)
      }
    }
  })
})
