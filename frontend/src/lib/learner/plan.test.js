import { describe, expect, it } from 'vitest'

import rewards from '../../config/rewards.json'
import { MEANINGS } from '../quiz/quiz'
import { LEVEL_IDS } from './learnerLevel'
import { EMPTY, LEVELS, PLAN_KEY, STEPS, factOf, goalXpOf, levelIdOf, levelOf, matches, readPlan, visibleSteps, writePlan } from './plan'

const ids = (steps) => steps.map((step) => step.id)
const stepOf = (id) => STEPS.find((step) => step.id === id)

describe('onboarding.json', () => {
  it('keeps the plan on the shelf under its own key', () => {
    expect(PLAN_KEY).toBe('plan')
  })

  it('branches only on questions asked before, with options they offer', () => {
    STEPS.forEach((step, at) => {
      for (const [id, allowed] of Object.entries(step.when ?? {})) {
        const earlier = STEPS.slice(0, at).find((one) => one.id === id)
        expect(earlier, `${step.id} waits on ${id}`).toBeDefined()
        expect(allowed.every((option) => earlier.options.some((one) => one.id === option))).toBe(true)
      }
    })
  })

  it('has a fact for every option of a step that shows facts', () => {
    for (const step of STEPS.filter((one) => one.fact)) {
      for (const option of step.options) expect(factOf(step, option.id), `${step.id}/${option.id}`).not.toBeNull()
    }
  })

  it('offers the meaning languages the quiz has, and daily goals the rewards offer', () => {
    expect(stepOf('lang').options.map((one) => one.id)).toEqual(Object.keys(MEANINGS))
    expect(stepOf('minutes').options.map((one) => one.xp)).toEqual(rewards.goals)
  })

  it('checks with one right answer per tap, and a level for every count', () => {
    const check = stepOf('check')
    expect(check.levels).toHaveLength(check.items.length + 1)
    for (const item of check.items) expect(item.options[item.right]).toBeDefined()
  })

  it('maps the levels it can say onto levels.json, plus 0 for the letters', () => {
    expect(Object.values(LEVELS.know)).toEqual(LEVEL_IDS.map((_, at) => at + 1))
    expect(LEVELS.read.no).toBe(0)
  })
})

describe('visibleSteps', () => {
  it('asks the dialect only of a speaker and the school only of a student of the sciences', () => {
    expect(ids(visibleSteps(EMPTY))).not.toContain('dialect')
    expect(ids(visibleSteps({ ...EMPTY, goals: ['speak'] }))).toContain('dialect')
    expect(ids(visibleSteps({ ...EMPTY, goals: ['understand', 'sciences'] }))).toContain('school')
  })

  it('skips what you know and the check for someone who cannot read yet', () => {
    expect(ids(visibleSteps({ ...EMPTY, read: 'no' }))).not.toContain('know')
    expect(ids(visibleSteps({ ...EMPTY, read: 'slow' }))).toEqual(expect.arrayContaining(['know', 'check']))
  })

  it('never runs past eight questions', () => {
    const most = { ...EMPTY, goals: ['speak', 'sciences'], read: 'yes' }
    expect(visibleSteps(most).length).toBeLessThanOrEqual(9)
    expect(visibleSteps(most).filter((step) => !step.items).length).toBeLessThanOrEqual(8)
  })

  it('matches nothing named as everything', () => {
    expect(matches(undefined, EMPTY)).toBe(true)
  })
})

describe('readPlan', () => {
  it('reads nothing, rubbish and a wrong type as nothing answered', () => {
    for (const raw of [null, '', 'not json', '42', '[]']) expect(readPlan(raw)).toEqual({ ...EMPTY })
  })

  it('drops options no longer offered and keeps at most two goals, first first', () => {
    const plan = readPlan({ goals: ['speak', 'astrology', 'speak', 'grammar', 'dawah'], minutes: '15', lang: 'ur' })
    expect(plan.goals).toEqual(['speak', 'grammar'])
    expect(plan.minutes).toBeNull()
    expect(plan.lang).toBe('ur')
  })

  it('drops the answer to a question no longer asked', () => {
    expect(readPlan({ goals: ['understand'], dialect: 'egyptian' }).dialect).toBeNull()
    expect(readPlan({ read: 'no', know: 'grammar', check: 3 })).toMatchObject({ know: null, check: null })
  })

  it('keeps a check only as a count it could be', () => {
    expect(readPlan({ read: 'yes', check: 2 }).check).toBe(2)
    for (const check of [-1, 4, 1.5, '2']) expect(readPlan({ read: 'yes', check }).check).toBeNull()
    expect(readPlan({ read: 'yes', keepSaid: true }).keepSaid).toBe(false)
  })

  it('comes back the same through writePlan', () => {
    const plan = readPlan({ goals: ['memorise'], read: 'slow', know: 'few', check: 3, keepSaid: true, hifz: 'amma', done: true })
    expect(readPlan(writePlan(plan))).toEqual(plan)
  })
})

describe('levelOf', () => {
  it('is nothing before it is answered', () => {
    expect(levelOf(EMPTY)).toBeNull()
    expect(levelIdOf(EMPTY)).toBeNull()
  })

  it('is 0 for someone who cannot read yet, starting at the first level', () => {
    expect(levelOf(readPlan({ read: 'no' }))).toBe(0)
    expect(levelIdOf(readPlan({ read: 'no' }))).toBe('beginner')
  })

  it('takes the check over what was said, unless what was said was kept', () => {
    const said = { read: 'yes', know: 'few', check: 2 }
    expect(levelIdOf(readPlan(said))).toBe('intermediate')
    expect(levelIdOf(readPlan({ ...said, keepSaid: true }))).toBe('beginner')
    expect(levelIdOf(readPlan({ read: 'yes', know: 'grammar' }))).toBe('advanced')
  })
})

describe('goalXpOf', () => {
  it('turns minutes into the daily XP goal', () => {
    expect(goalXpOf(readPlan({ minutes: '10' }))).toBe(50)
    expect(goalXpOf(EMPTY)).toBeNull()
  })
})
