import { describe, expect, it } from 'vitest'
import { CHECK, MISSED, SAID, WRONG } from './follow'
import {
  afterRecitation, becomesLearnt, groupsOf, isClean, isLearnt, loadRecord, markRecitation, nodeState, pageOf, reactionTo, saveRecord, score, tally, tiersOf,
  today, unlocked, upNext,
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

describe('learnt and the score', () => {
  const PATH = { steps: [{ id: 'takbir' }, { id: 'ruku' }] }

  it('needs clean runs on two different days, not two runs on one day', () => {
    let record = afterRecitation({}, 'takbir', true, '2026-09-28')
    record = afterRecitation(record, 'takbir', true, '2026-09-28')
    expect(isLearnt(record, 'takbir')).toBe(false)
    record = afterRecitation(record, 'takbir', true, '2026-09-29')
    expect(isLearnt(record, 'takbir')).toBe(true)
    expect(record.takbir.tries).toBe(3)
  })

  it('counts a run that was not clean as a try and nothing more', () => {
    const record = afterRecitation({}, 'ruku', false, '2026-09-28')
    expect(record.ruku).toEqual({ tries: 1, cleanDays: [] })
  })

  it('scores only what is learnt, never what was tried', () => {
    let record = afterRecitation({}, 'ruku', false, '2026-09-28')
    record = afterRecitation(record, 'ruku', false, '2026-09-29')
    expect(score(PATH, record)).toEqual({ learnt: 0, total: 2 })
    record = afterRecitation(afterRecitation(record, 'takbir', true, '2026-09-28'), 'takbir', true, '2026-09-30')
    expect(score(PATH, record)).toEqual({ learnt: 1, total: 2 })
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

describe('the map', () => {
  const DAYS = ['2026-09-28', '2026-09-29']
  const learnt = { tries: 2, cleanDays: DAYS }
  const step = (id) => ({ id })
  const PATH = { id: 'salah', tier: 'basics', steps: [step('takbir'), step('ruku')], groups: [{ id: 'g', steps: ['takbir', 'ruku'] }] }
  const TIERS = tiersOf(
    [{ id: 'basics' }, { id: 'next', proposed: [{ id: 'p', title: 'P', about: 'About P' }] }, { id: 'last' }],
    [PATH],
  )

  it('still counts a record saved before the map existed as learnt', () => {
    // The same shape loadRecord has always written: no migration, no new field.
    expect(nodeState([step('takbir')], { takbir: learnt })).toBe('learnt')
  })

  it('says locked, open, started, learnt, and a group is learnt only when every step is', () => {
    const both = [step('takbir'), step('ruku')]
    expect(nodeState(both, {}, false)).toBe('locked')
    expect(nodeState(both, {})).toBe('open')
    expect(nodeState(both, { ruku: { tries: 1, cleanDays: [] } })).toBe('started')
    expect(nodeState(both, { takbir: learnt })).toBe('started')
    expect(nodeState(both, { takbir: learnt, ruku: learnt })).toBe('learnt')
    expect(nodeState([], {})).toBe('open')
  })

  it('opens a tier only once every step before it is learnt, and never one nobody wrote', () => {
    expect(unlocked(TIERS, 0, {})).toBe(true)
    expect(unlocked(TIERS, 1, {})).toBe(false)
    const done = { takbir: learnt, ruku: learnt }
    // The next tier has no path yet, so it stays shut however much is learnt.
    expect(unlocked(TIERS, 1, done)).toBe(false)
    const written = tiersOf([{ id: 'basics' }, { id: 'next' }, { id: 'last' }], [PATH, { ...PATH, id: 'b', tier: 'next', steps: [step('x')] }])
    expect(unlocked(written, 1, {})).toBe(false)
    expect(unlocked(written, 1, done)).toBe(true)
    expect(unlocked(written, 2, done)).toBe(false)
  })

  it('shows a tier without paths as one locked group of its proposed topics', () => {
    const [group] = groupsOf(TIERS[1])
    expect(group.steps).toEqual([{ id: 'p', title: 'P', meaning: 'About P', proposed: true }])
    expect(groupsOf(TIERS[0])[0].steps.map((one) => one.id)).toEqual(['takbir', 'ruku'])
  })

  it('points at the first step not yet learnt, and at none once the open tiers are done', () => {
    expect(upNext(TIERS, {}).id).toBe('takbir')
    expect(upNext(TIERS, { takbir: learnt }).id).toBe('ruku')
    expect(upNext(TIERS, { takbir: learnt, ruku: learnt })).toBeNull()
  })

  it('celebrates only the run that makes a step learnt', () => {
    const before = { takbir: { tries: 1, cleanDays: ['2020-01-01'] } }
    expect(becomesLearnt(before, 'takbir', true)).toBe(true)
    // A second clean run on the same day adds no day, so it makes nothing.
    expect(becomesLearnt({ takbir: { tries: 1, cleanDays: [today()] } }, 'takbir', true)).toBe(false)
    expect(becomesLearnt(before, 'takbir', false)).toBe(false)
    expect(becomesLearnt({}, 'takbir', false)).toBe(false)
    expect(becomesLearnt({ takbir: learnt }, 'takbir', true)).toBe(false)
  })

  it('gives Qalam a nod, a droop, or a hop for a run of right ones', () => {
    expect(reactionTo(true, 1)).toBe('correct')
    expect(reactionTo(false, 0)).toBe('wrong')
    expect(reactionTo(true, 3)).toBe('streak')
  })
})
