/**
 * The book is the set you are meant to work through, so nothing else should hand
 * you a word it already teaches. These check the subtraction really happens, on
 * the real cuts, and that it stops exactly where it should; at the book itself.
 *
 * The subtraction now happens once, when the cuts are built, instead of in the
 * browser on every load. What it matches on matters: same letters AND the same
 * type of word. هُدًى (guidance, a noun) and هَدَى (he guided, a verb) share
 * their letters and are not the same word, so teaching one does not teach the
 * other.
 */
import { describe, expect, it, vi } from 'vitest'

import cuts from '../../public/words/cuts.json'
import index from '../../public/words/index.json'
import allWords from '../../public/words/words.json'
import { bareForm, hasDiacritics } from './arabicText'
import { wordsFor } from './quizBanks'

const FILES = {
  '/words/words.json': allWords,
  '/words/cuts.json': cuts,
  '/words/index.json': index,
}
vi.stubGlobal('fetch', vi.fn(async (path) => ({ ok: true, json: async () => FILES[path] })))

const cut = (name) => cuts[name].map((at) => allWords.words[at])
const identity = (word) => `${bareForm(word.ar)}/${word.wordType}`

describe('the everyday set', () => {
  // Not filtered at run time: vocabulary.json is built with no Qur'anic word in
  // it, so the set is disjoint by construction. This is the guard on the data.
  it("shares not one word with the Qur'an, the book list or the corpus", () => {
    const quranic = new Set([...cuts.book, ...cuts.quran])
    expect(quranic.size).toBeGreaterThan(1000) // guards the test itself
    const shared = cuts.everyday.filter((at) => quranic.has(at))
    expect(shared.map((at) => allWords.words[at].ar)).toEqual([])
  })

  it('is handed back whole, with nothing subtracted', async () => {
    expect(await wordsFor('everyday')).toEqual(cut('everyday'))
  })
})

describe('a surah or a juz', () => {
  const taught = new Set(cut('book').map(identity))

  it('never hands back a word the book already teaches', async () => {
    for (const name of ['surah:2', 'surah:105', 'juz:1', 'juz:30']) {
      const [source, key] = name.split(':')
      const words = await wordsFor('quranic', `${source}:${key}`)
      expect(words.length, name).toBeGreaterThan(0)
      expect(words.filter((w) => taught.has(identity(w))).map((w) => w.ar), name).toEqual([])
    }
  })

  it('keeps a word that only looks like one the book teaches', () => {
    // Same letters, different type; a different word, so it stays askable.
    const lookalikes = cut('surah:2').filter(
      (word) => !taught.has(identity(word))
        && cut('book').some((known) => bareForm(known.ar) === bareForm(word.ar)),
    )
    expect(lookalikes.length).toBeGreaterThan(0)
  })
})

describe('the book itself', () => {
  it('is never subtracted from, it is the reference set', async () => {
    const group = index.sets.find((set) => set.id === 'book').groups[0].id
    const words = await wordsFor('quranic', `book:${group}`)
    expect(words.length).toBeGreaterThan(0)
    expect(words).toEqual(cut(`book:${group}`))
  })

  it('keeps every one of its own words when asked for the whole set', async () => {
    expect(await wordsFor('quranic')).toHaveLength(cuts.book.length)
  })
})

describe('matching two spellings of one word', () => {
  it('ignores the vowel marks and the shape of the alif', () => {
    expect(bareForm('كِتَاب')).toBe(bareForm('كتاب'))
    expect(bareForm('أَب')).toBe(bareForm('اب'))
    expect(bareForm('إِنّ')).toBe(bareForm('ان'))
  })

  it('does not merge two genuinely different words', () => {
    expect(bareForm('عَلَم')).not.toBe(bareForm('عَالَم'))
    expect(bareForm('حَيَاة')).not.toBe(bareForm('حَيَاه'))
  })

  it('spots harakat only when they are there', () => {
    expect(hasDiacritics('كِتَاب')).toBe(true)
    expect(hasDiacritics('كتاب')).toBe(false)
    expect(hasDiacritics('')).toBe(false)
  })
})
