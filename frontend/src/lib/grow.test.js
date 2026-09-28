import { describe, expect, it } from 'vitest'
import { CHECK, MISSED, SAID, WRONG } from './follow'
import {
  afterRecitation, isClean, isMastered, loadRecord, markRecitation, nextStep, pageOf, saveRecord, score, tally, today,
} from './grow'

const RUKU = ['سُبْحَانَ', 'رَبِّيَ', 'الْعَظِيمِ']
const states = (marks) => marks.words.map((mark) => mark.state)

describe('marking one recitation', () => {
  it('marks every word right when every word was said and the sound agrees', () => {
    const marks = markRecitation(RUKU, 'سبحان ربي العظيم', [0.99, 0.99, 0.99])
    expect(states(marks)).toEqual([SAID, SAID, SAID])
    expect(isClean(marks)).toBe(true)
  })

  it('never calls a doubtful word right, so a run with one is not clean', () => {
    // Heard as another word, and the sound half agrees: at beginner that is
    // doubt, orange, and not a pass.
    const marks = markRecitation(RUKU, 'سبحان ربي الكريم', [0.99, 0.99, 0.8], 'beginner')
    expect(states(marks)).toEqual([SAID, SAID, CHECK])
    expect(isClean(marks)).toBe(false)
  })

  it('does not accuse a word the sound never checked; it is only not sure', () => {
    const marks = markRecitation(RUKU, 'سبحان ربي الكريم', [])
    expect(states(marks)[2]).toBe(CHECK)
  })

  it('marks a word wrong when the sound says so', () => {
    const marks = markRecitation(RUKU, 'سبحان ربي الكريم', [0.99, 0.99, 0.01])
    expect(states(marks)[2]).toBe(WRONG)
  })

  it('marks a one-word step, which the page follower would never start on', () => {
    expect(states(markRecitation(['آمِينَ'], 'امين', [0.99]))).toEqual([SAID])
    expect(states(markRecitation(['آمِينَ'], 'قال', [0.01]))).toEqual([WRONG])
  })

  it('says nothing of the step was heard as not said, and lets the sound rescue it', () => {
    expect(states(markRecitation(RUKU, 'موسيقى', [0.01, 0.01, 0.01]))).toEqual([MISSED, MISSED, MISSED])
    expect(states(markRecitation(RUKU, 'موسيقى', [0.99, 0.99, 0.99]))).toEqual([SAID, SAID, SAID])
  })

  it('counts each state for the line under the recitation', () => {
    const marks = markRecitation(RUKU, 'سبحان ربك العظيم', [0.99, 0.8, 0.01], 'beginner')
    expect(tally(marks)).toEqual({ [SAID]: 1, [CHECK]: 1, [WRONG]: 1, [MISSED]: 0 })
  })
})

describe('a step as words', () => {
  it('splits a phrase into its written words', () => {
    expect(pageOf({ arabic: 'سُبْحَانَ رَبِّيَ الْعَظِيمِ' }).words).toEqual(RUKU)
  })

  it('runs ayahs together and remembers where each one starts', () => {
    const page = pageOf({ ayahs: ['112:1', '112:2'] }, { '112:1': 'قُلْ هُوَ ٱللَّهُ أَحَدٌ', '112:2': 'ٱللَّهُ ٱلصَّمَدُ' })
    expect(page.words).toHaveLength(6)
    expect(page.ayahs).toEqual([{ key: '112:1', from: 0, count: 4 }, { key: '112:2', from: 4, count: 2 }])
  })
})

describe('mastery and the score', () => {
  const PATH = { steps: [{ id: 'takbir' }, { id: 'ruku' }] }

  it('needs clean runs on two different days, not two runs on one day', () => {
    let record = afterRecitation({}, 'takbir', true, '2026-09-28')
    record = afterRecitation(record, 'takbir', true, '2026-09-28')
    expect(isMastered(record, 'takbir')).toBe(false)
    record = afterRecitation(record, 'takbir', true, '2026-09-29')
    expect(isMastered(record, 'takbir')).toBe(true)
    expect(record.takbir.tries).toBe(3)
  })

  it('counts a run that was not clean as a try and nothing more', () => {
    const record = afterRecitation({}, 'ruku', false, '2026-09-28')
    expect(record.ruku).toEqual({ tries: 1, cleanDays: [] })
  })

  it('scores only what is mastered, never what was tried', () => {
    let record = afterRecitation({}, 'ruku', false, '2026-09-28')
    record = afterRecitation(record, 'ruku', false, '2026-09-29')
    expect(score(PATH, record)).toEqual({ mastered: 0, total: 2 })
    record = afterRecitation(afterRecitation(record, 'takbir', true, '2026-09-28'), 'takbir', true, '2026-09-30')
    expect(score(PATH, record)).toEqual({ mastered: 1, total: 2 })
  })

  it('opens on the first step not yet mastered', () => {
    const record = { takbir: { tries: 2, cleanDays: ['2026-09-28', '2026-09-29'] } }
    expect(nextStep(PATH, record).id).toBe('ruku')
    expect(nextStep(PATH, {}).id).toBe('takbir')
  })

  it('writes today as the reader\'s own date', () => {
    expect(today(new Date(2026, 0, 5))).toBe('2026-01-05')
  })
})

describe('the record in storage', () => {
  const memory = () => {
    const kept = {}
    return { getItem: (k) => kept[k] ?? null, setItem: (k, v) => { kept[k] = v } }
  }

  it('comes back as it was saved', () => {
    const storage = memory()
    const record = afterRecitation({}, 'takbir', true, '2026-09-28')
    saveRecord(record, storage)
    expect(loadRecord(storage)).toEqual(record)
  })

  it('is empty, not an error, when storage holds nonsense or throws', () => {
    expect(loadRecord({ getItem: () => '{not json' })).toEqual({})
    expect(loadRecord({ getItem: () => { throw new Error('blocked') } })).toEqual({})
    expect(() => saveRecord({}, { setItem: () => { throw new Error('full') } })).not.toThrow()
  })

  it('drops what a record should not hold', () => {
    const storage = { getItem: () => JSON.stringify({ a: { tries: -3, cleanDays: ['2026-09-28', '2026-09-28', 'x', 5] } }) }
    expect(loadRecord(storage)).toEqual({ a: { tries: 0, cleanDays: ['2026-09-28'] } })
  })
})
