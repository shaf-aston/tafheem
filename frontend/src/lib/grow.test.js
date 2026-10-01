import { describe, expect, it } from 'vitest'
import { CHECK, MISSED, SAID, WRONG } from './follow'
import { byHand } from './growKinds'
import {
  afterDone, afterRecitation, becomesLearnt, daysOf, groupsOf, isLearnt, judge, mapOf, nodeState, pageOf, reactionTo, score, tally, tiersOf,
  today, unlocked, upNext,
} from './grow'

const RUKU = ['سُبْحَانَ', 'رَبِّيَ', 'الْعَظِيمِ']
const states = (marks) => marks.words.map((mark) => mark.state)
// Marks only, at the reader's own checking level unless one is named.
const mark = (words, text, sure, level = 'standard') => judge(words, text, sure, level).marks

describe('marking one recitation', () => {
  it('marks every word right when every word was said and the sound agrees', () => {
    const marks = mark(RUKU, 'سبحان ربي العظيم', [0.99, 0.99, 0.99])
    expect(states(marks)).toEqual([SAID, SAID, SAID])
    expect(judge(RUKU, 'سبحان ربي العظيم', [0.99, 0.99, 0.99], 'standard')).toMatchObject({ clean: true, weighed: true })
  })

  it('never calls a doubtful word right, so a run with one is not clean', () => {
    // Heard as another word, and the sound half agrees: at beginner that is
    // doubt, orange, and not a pass.
    const marks = mark(RUKU, 'سبحان ربي الكريم', [0.99, 0.99, 0.8], 'beginner')
    expect(states(marks)).toEqual([SAID, SAID, CHECK])
    expect(judge(RUKU, 'سبحان ربي الكريم', [0.99, 0.99, 0.8], 'beginner').clean).toBe(false)
  })

  it('is never clean when the sound was not weighed for every word, however right it reads', () => {
    for (const sure of [null, [], [0.99, 0.99]]) {
      expect(judge(RUKU, 'سبحان ربي العظيم', sure, 'standard')).toMatchObject({ clean: false, weighed: false })
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
    const marks = mark(RUKU, 'سبحان ربك العظيم', [0.99, 0.8, 0.01], 'beginner')
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

describe('learnt and the score', () => {
  const TIERS = [{ paths: [{ steps: [{ id: 'takbir' }, { id: 'ruku' }] }] }]

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

  it('scores only what is learnt, never what was tried', () => {
    let record = afterRecitation({}, 'ruku', false, '2026-09-28')
    record = afterRecitation(record, 'ruku', false, '2026-09-29')
    expect(score(TIERS, record)).toEqual({ learnt: 0, total: 2 })
    record = afterRecitation(afterRecitation(record, 'takbir', true, '2026-09-28'), 'takbir', true, '2026-09-30')
    expect(score(TIERS, record)).toEqual({ learnt: 1, total: 2 })
  })

  it('makes a posture learnt on one Done, with no days to count', () => {
    const record = afterDone({}, 'bow-down')
    expect(isLearnt(record, 'bow-down')).toBe(true)
    expect(nodeState([{ id: 'bow-down' }], record)).toBe('learnt')
    expect(daysOf(record, 'bow-down')).toBe(0)
    expect(score(TIERS, afterDone({}, 'ruku'))).toEqual({ learnt: 1, total: 2 })
  })

  it('leaves the other steps of the record alone when a posture is done', () => {
    const before = afterRecitation({}, 'takbir', true, '2026-09-28')
    expect(afterDone(before, 'stand-up').takbir).toBe(before.takbir)
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

describe('the map', () => {
  const DAYS = ['2026-09-28', '2026-09-29']
  const learnt = { tries: 2, cleanDays: DAYS }
  const step = (id) => ({ id })
  const PATH = { id: 'salah', tier: 'basics', steps: [step('takbir'), step('ruku')], groups: [{ id: 'g', steps: ['takbir', 'ruku'] }] }
  const TIERS = tiersOf(
    [{ id: 'basics' }, { id: 'next', proposed: [{ id: 'p', title: 'P', about: 'About P' }] }, { id: 'last', proposed: [] }],
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
    expect(group.steps).toEqual([{ id: 'p', title: 'P', ayahs: [], meaning: 'About P', proposed: true }])
    expect(groupsOf(TIERS[0])[0].steps.map((one) => one.id)).toEqual(['takbir', 'ruku'])
  })

  it('shows a locked tier with nothing proposed as no groups, not an empty one', () => {
    expect(groupsOf(TIERS[2])).toEqual([])
  })

  it('lays out each tier for the map: paths, group states, the step up next, and alongside groups apart', () => {
    const along = { ...PATH, groups: [...PATH.groups, { id: 'care', alongside: true, steps: ['ruku'] }] }
    const [first, second] = mapOf(tiersOf([{ id: 'basics' }, { id: 'next', proposed: [] }], [along]), { takbir: learnt }, along.steps[1])
    expect(first).toMatchObject({ open: true, learnt: 1, total: 3 })
    const [salah] = first.paths
    expect(salah.groups.map((one) => one.group.id)).toEqual(['g'])
    expect(salah.alongside.map((one) => one.group.id)).toEqual(['care'])
    expect(salah.groups[0]).toMatchObject({ state: 'started', learnt: 1 })
    expect(salah.groups[0].steps.map((one) => [one.state, one.now])).toEqual([['learnt', false], ['open', true]])
    expect(second).toMatchObject({ open: false, total: 0, paths: [{ groups: [], alongside: [] }] })
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
