import { describe, expect, it } from 'vitest'
import { CHECK, MISSED, SAID, WRONG } from './follow'
import { byHand } from './grow/cards'
import {
  afterRecitation, becomesLearnt, daysOf, isClean, isLearnt, judge, pageOf, tally, today,
} from './grow'

const RUKU = ['سُبْحَانَ', 'رَبِّيَ', 'الْعَظِيمِ']
const states = (marks) => marks.words.map((mark) => mark.state)
// Marks only.
// The ear's numbers as judge takes them: a { sure } per word, null for none.
const scored = (sure) => sure && Array.from(sure, (s) => (s == null ? null : { sure: s }))
const mark = (words, text, sure) => judge(words, text, scored(sure)).marks

describe('marking one recitation', () => {
  it('marks every word right when every word was said and the sound agrees', () => {
    const marks = mark(RUKU, 'سبحان ربي العظيم', [0.99, 0.99, 0.99])
    expect(states(marks)).toEqual([SAID, SAID, SAID])
    expect(judge(RUKU, 'سبحان ربي العظيم', scored([0.99, 0.99, 0.99]))).toMatchObject({ clean: true, weighed: true })
  })

  it('never calls a doubtful word right, so a run with one is not clean', () => {
    // Heard as another word, and the sound never weighed it: that is doubt,
    // orange, and not a pass.
    const marks = mark(RUKU, 'سبحان ربي الكريم', [0.99, 0.99])
    expect(states(marks)).toEqual([SAID, SAID, CHECK])
    expect(judge(RUKU, 'سبحان ربي الكريم', scored([0.99, 0.99])).clean).toBe(false)
  })

  it('is never clean when the sound was not weighed for every word, however right it reads', () => {
    for (const sure of [null, [], [0.99, 0.99]]) {
      expect(judge(RUKU, 'سبحان ربي العظيم', scored(sure), 'standard')).toMatchObject({ clean: false, weighed: false })
    }
  })

  it('never counts an empty ayah as a try', () => {
    expect(judge([], '', [], 'standard')).toMatchObject({ clean: false, weighed: false })
  })

  it('does not accuse a word the sound never checked; it is only not sure', () => {
    const marks = mark(RUKU, 'سبحان ربي الكريم', [])
    expect(states(marks)[2]).toBe(CHECK)
  })

  it('marks a word wrong when the sound says so', () => {
    const marks = mark(RUKU, 'سبحان ربي الكريم', [0.99, 0.99, 0.01])
    expect(states(marks)[2]).toBe(WRONG)
  })

  it('marks a one-word step, which the page follower would never start on', () => {
    expect(states(mark(['آمِينَ'], 'امين', [0.99]))).toEqual([SAID])
    expect(states(mark(['آمِينَ'], 'قال', [0.01]))).toEqual([WRONG])
  })

  it('says nothing of the step was heard as not said, and lets the sound rescue it', () => {
    expect(states(mark(RUKU, 'موسيقى', [0.01, 0.01, 0.01]))).toEqual([MISSED, MISSED, MISSED])
    expect(states(mark(RUKU, 'موسيقى', [0.99, 0.99, 0.99]))).toEqual([SAID, SAID, SAID])
  })

  it('counts each state for the line under the recitation', () => {
    const marks = mark(RUKU, 'سبحان ربك العظيم', [0.99, undefined, 0.01])
    expect(tally(marks)).toEqual({ [SAID]: 1, [CHECK]: 1, [WRONG]: 1, [MISSED]: 0 })
  })
})

describe('a step as words', () => {
  it('splits a phrase into its written words', () => {
    expect(pageOf({ arabic: 'سُبْحَانَ رَبِّيَ الْعَظِيمِ', ayahs: [] }).words).toEqual(RUKU)
  })

  it('runs ayahs together and remembers where each one starts', () => {
    const page = pageOf({ ayahs: ['112:1', '112:2'] }, { '112:1': 'قُلْ هُوَ ٱللَّهُ أَحَدٌ', '112:2': 'ٱللَّهُ ٱلصَّمَدُ' })
    expect(page.words).toHaveLength(6)
    expect(page.ayahs).toEqual([{ key: '112:1', from: 0, count: 4 }, { key: '112:2', from: 4, count: 2 }])
  })
})

describe('learnt', () => {
  it('needs clean runs on two different days, not two runs on one day', () => {
    let record = afterRecitation({}, 'takbir', true, '2026-09-28')
    record = afterRecitation(record, 'takbir', true, '2026-09-28')
    expect(isLearnt(record, 'takbir')).toBe(false)
    record = afterRecitation(record, 'takbir', true, '2026-09-29')
    expect(isLearnt(record, 'takbir')).toBe(true)
    expect(record.takbir.tries).toBe(3)
    expect(daysOf(record, 'takbir')).toBe(2)
    expect(daysOf(record, 'never')).toBe(0)
  })

  it('counts a run that was not clean as a try and nothing more', () => {
    const record = afterRecitation({}, 'ruku', false, '2026-09-28')
    expect(record.ruku).toEqual({ tries: 1, cleanDays: [] })
  })

  it('says a step becomes learnt only on the clean run that tips it over', () => {
    const once = afterRecitation({}, 'takbir', true, '2026-09-28')
    expect(becomesLearnt({}, 'takbir', true)).toBe(false)
    expect(becomesLearnt(once, 'takbir', false)).toBe(false)
    expect(becomesLearnt(once, 'takbir', true)).toBe(true)
    expect(becomesLearnt(afterRecitation(once, 'takbir', true, '2026-09-29'), 'takbir', true)).toBe(false)
  })

  it('ticks off by hand only the steps of kind action', () => {
    expect(byHand({ kind: 'action', ayahs: [] })).toBe(true)
    expect(byHand({ kind: null, arabic: 'اللَّهُ أَكْبَرُ', ayahs: [] })).toBe(false)
    expect(byHand({ kind: null, ayahs: ['112:1'] })).toBe(false)
  })

  it('writes today as the reader\'s own date', () => {
    expect(today(new Date(2026, 0, 5))).toBe('2026-01-05')
  })
})

describe('where the one-word rule ends and the page follower begins', () => {
  // recite.json's anchor-words is 2: a step shorter than that is judged word by
  // word, one that long goes through the follower, which waits for two words.
  const SUBHAN = ['سُبْحَانَ', 'رَبِّيَ']

  it('judges a one-word step on any word heard, so a wrong one is wrong', () => {
    expect(states(mark(['آمِينَ'], 'قال', [0.01]))).toEqual([WRONG])
  })

  it('waits for two words on a two-word step, so one word heard marks nothing said', () => {
    expect(states(mark(SUBHAN, 'سبحان', [0.01, 0.01]))).toEqual([MISSED, MISSED])
  })

  it('marks a two-word step said whole as right, through the follower', () => {
    expect(states(mark(SUBHAN, 'سبحان ربي', [0.99, 0.99]))).toEqual([SAID, SAID])
  })
})

describe('nothing heard at all', () => {
  it('is not said, for a one-word step and a longer one alike', () => {
    expect(states(mark(['آمِينَ'], '', [0.01]))).toEqual([MISSED])
    expect(states(mark(RUKU, '', [0.01, 0.01, 0.01]))).toEqual([MISSED, MISSED, MISSED])
  })

  it('is never clean', () => {
    expect(judge(RUKU, '', scored([0.01, 0.01, 0.01])).clean).toBe(false)
  })
})

describe('isClean', () => {
  it('is false for no words, rather than vacuously true', () => {
    expect(isClean({ words: [] })).toBe(false)
  })

  it('is true only when every word was said', () => {
    expect(isClean({ words: [{ state: SAID }, { state: SAID }] })).toBe(true)
    expect(isClean({ words: [{ state: SAID }, { state: CHECK }] })).toBe(false)
  })
})
