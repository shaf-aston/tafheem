/**
 * The Qur'anic set differs from the everyday one in a way that matters: it is
 * copied from a book, and the book lists real synonyms; three separate words
 * all glossed "reward". So meaning keys here are deliberately NOT unique. What
 * must hold instead is that no single question ever shows two of them, and that
 * narrowing to one group still produces a full, fair question.
 *
 * Asserted against the files the app actually fetches, with fetch answering
 * from them, so a build that breaks a cut breaks a test.
 */
import { describe, expect, it, vi } from 'vitest'

import cuts from '../../public/words/cuts.json'
import index from '../../public/words/index.json'
import allWords from '../../public/words/words.json'
import { buildQuestion, DIRECTIONS, makeRandom } from './quiz'
import { BANKS, WHOLE_SET_SCOPES, wordsFor } from './quizBanks'

const FILES = {
  '/words/words.json': allWords,
  '/words/cuts.json': cuts,
  '/words/index.json': index,
}
vi.stubGlobal('fetch', vi.fn(async (path) => ({ ok: true, json: async () => FILES[path] })))

const cut = (name) => cuts[name].map((at) => allWords.words[at])

const BANK = cut('book')
const GROUP_IDS = index.sets.find((set) => set.id === 'book').groups.map((g) => g.id)
const DIRECTION_IDS = Object.keys(DIRECTIONS)

const rounds = (words, direction, n = 120) =>
  Array.from({ length: n }, (_, seed) =>
    buildQuestion(words, { direction, random: makeRandom(seed + 1) }),
  )

describe('the Qur\'anic word list', () => {
  it('fills in every field the quiz reads', () => {
    for (const word of BANK) {
      expect(word.ar, JSON.stringify(word)).toBeTruthy()
      expect(word.en, JSON.stringify(word)).toBeTruthy()
      expect(word.meaningKey, JSON.stringify(word)).toBeTruthy()
      expect(word.groups, JSON.stringify(word)).toBeTruthy()
      expect(['noun', 'verb', 'adjective'], JSON.stringify(word)).toContain(word.wordType)
    }
  })

  it('never spells two different entries the same way in either language', () => {
    // Two rows reading ذَهَبَ with different meanings would make an
    // Arabic-to-English question unanswerable, however the options fall.
    const byArabic = new Map()
    for (const word of BANK) {
      const clash = byArabic.get(word.ar)
      expect(clash, `${word.ar} appears twice: ${clash?.en} / ${word.en}`).toBeUndefined()
      byArabic.set(word.ar, word)
    }
    const byEnglish = new Map()
    for (const word of BANK) {
      const clash = byEnglish.get(word.en)
      // Same wording is only allowed when the entries are declared synonyms.
      if (clash) expect(clash.meaningKey, `"${word.en}" repeats`).toBe(word.meaningKey)
      byEnglish.set(word.en, word)
    }
  })

  it('puts every word in a declared group, and every group to work', async () => {
    const declared = new Set(GROUP_IDS.map((id) => `book:${id}`))
    for (const word of BANK) {
      const own = word.groups.filter((group) => group.startsWith('book:'))
      expect(own, JSON.stringify(word)).toHaveLength(1)
      expect(declared.has(own[0]), `unknown group ${own[0]}`).toBe(true)
    }
    for (const id of GROUP_IDS) {
      expect((await wordsFor('quranic', `book:${id}`)).length, `${id} is empty`).toBeGreaterThan(0)
    }
  })

  it('leaves every group big enough to fill a four-option question by itself', async () => {
    for (const id of GROUP_IDS) {
      const meanings = new Set((await wordsFor('quranic', `book:${id}`)).map((w) => w.meaningKey))
      expect(meanings.size, `${id} has only ${meanings.size} distinct meanings`).toBeGreaterThanOrEqual(4)
    }
  })
})

describe.each(DIRECTION_IDS)('Qur\'anic questions, %s', (direction) => {
  const questions = rounds(BANK, direction)

  it('always offers four options with the answer among them exactly once', () => {
    for (const q of questions) {
      expect(q.options).toHaveLength(4)
      expect(q.options.filter((o) => o.id === q.answerId)).toHaveLength(1)
    }
  })

  it('never puts two words of the same meaning side by side', () => {
    for (const q of questions) {
      const meanings = q.options.map((o) => o.id)
      expect(new Set(meanings).size, JSON.stringify(meanings)).toBe(4)
      const texts = q.options.map((o) => o.text)
      expect(new Set(texts).size, JSON.stringify(texts)).toBe(4)
    }
  })

  it('keeps the prompt out of the answer list', () => {
    for (const q of questions) {
      expect(q.options.map((o) => o.text)).not.toContain(q.prompt)
    }
  })
})

describe('narrowing to one group', () => {
  it('draws both the answer and every wrong option from that group alone', async () => {
    for (const id of GROUP_IDS) {
      const words = await wordsFor('quranic', `book:${id}`)
      const inGroup = new Set(words.map((w) => w.meaningKey))
      for (const q of rounds(words, 'ar-en', 20)) {
        expect(q.options).toHaveLength(4)
        for (const option of q.options) {
          expect(inGroup.has(option.id), `${option.text} is not in ${id}`).toBe(true)
        }
      }
    }
  })
})

describe('the bank registry', () => {
  it('offers every set and rejects one it does not have', async () => {
    // Qur'anic first: it is the default, and the pills read in that order.
    // "All" is last of the cuts because it is the widest, and Mistakes last of
    // all: it is not a cut of the table but whatever the learner still owes.
    expect(Object.keys(BANKS)).toEqual(['quranic', 'everyday', 'all', 'mistakes'])
    expect(await wordsFor('quranic')).toHaveLength(BANK.length)
    await expect(wordsFor('nope')).rejects.toThrow(/Unknown quiz bank/)
  })

  it('treats an empty group id as "the whole set", not "no words"', async () => {
    expect(await wordsFor('quranic', '')).toHaveLength(BANK.length)
  })
})

describe('the All set', () => {
  it('is every word there is, once each; no merging, nothing to de-duplicate', async () => {
    // Every list now points into one array of words, so a word shared by two
    // lists is one entry rather than a copy in each that has to be collapsed.
    const words = await wordsFor('all')
    expect(words).toHaveLength(allWords.words.length)
    const spellings = words.map((w) => w.ar)
    expect(new Set(spellings).size).toBe(spellings.length)
    for (const word of BANK) expect(spellings).toContain(word.ar)
  })
})

describe("the Whole Qur'an scope", () => {
  it('keeps the words the book teaches, unlike a surah or a juz', async () => {
    const words = await wordsFor('quranic', 'quran:all')
    const inTheBook = new Set(BANK.map((w) => w.ar))
    expect(words.some((w) => inTheBook.has(w.ar))).toBe(true)
    expect(words.length).toBeGreaterThan(BANK.length)
  })

  it('is offered as a whole-set choice, beside the book, with no second picker', () => {
    expect(WHOLE_SET_SCOPES.map((s) => s.id)).toEqual(['all', 'quran'])
    expect(WHOLE_SET_SCOPES.find((s) => s.id === 'quran').group).toBe('quran:all')
  })
})
