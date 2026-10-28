import { describe, expect, it } from 'vitest'

import { worldOf } from '../grow/worlds'
import { LISTED } from '../nav/tabs'
import { readPlan, STEPS } from './plan'
import { PLACES, RANK, recommend } from './recommend'

const NOW = Date.parse('2026-10-28T12:00:00Z')
const ago = (days) => new Date(NOW - days * 864e5).toISOString()
const row = (module, attempts, correct, days) => ({ module, attempts, correct, learnt: 0, lastAt: ago(days) })
const top = (plan, modules = [], n = 3) => recommend(readPlan(plan), modules, NOW).slice(0, n).map((one) => one.place.id)

// The four learners the plan was drawn up with: this table is the ranking's acceptance test.
const AISHA = { goals: ['understand'], read: 'no', lang: 'en', hifz: 'none', minutes: '5' }
const BILAL = { goals: ['understand', 'memorise'], read: 'yes', know: 'few', lang: 'en', hifz: 'amma', minutes: '10' }
const OMAR = { goals: ['speak', 'understand'], read: 'slow', know: 'few', lang: 'en', hifz: 'none', dialect: 'egyptian', minutes: '10' }
const FATIMA = { goals: ['sciences', 'grammar'], read: 'yes', know: 'grammar', lang: 'ur', hifz: 'few', school: 'shafii', minutes: '20' }

describe('onboarding.json places', () => {
  const goals = STEPS.find((step) => step.id === 'goals').options.map((option) => option.id)

  it('names a world in worlds.json or a tab a person can open, never both', () => {
    for (const place of PLACES) {
      expect(Boolean(place.world) !== Boolean(place.tab), place.id).toBe(true)
      if (place.world) expect(worldOf(place.world), place.id).not.toBeNull()
      if (place.tab) expect(LISTED.some((tab) => tab.id === place.tab), place.id).toBe(true)
    }
  })

  it('serves only goals that are asked, by 0 to 1, over a band from 0 to 3', () => {
    for (const place of PLACES) {
      for (const [goal, weight] of Object.entries(place.goals)) {
        expect(goals, place.id).toContain(goal)
        expect(weight).toBeGreaterThan(0)
        expect(weight).toBeLessThanOrEqual(1)
      }
      const [low, high] = place.band
      expect(0 <= low && low <= high && high <= 3, place.id).toBe(true)
    }
  })

  it('gives every goal somewhere to go', () => {
    for (const goal of goals) expect(PLACES.some((place) => place.goals[goal]), goal).toBe(true)
  })

  it('has unique ids', () => {
    expect(new Set(PLACES.map((place) => place.id)).size).toBe(PLACES.length)
  })
})

describe('recommend: the four learners', () => {
  it('starts someone who cannot read yet on Basics, then Prayer and Words', () => {
    expect(top(AISHA)).toEqual(['basics', 'prayer', 'words'])
  })

  it('gives a reader with few words the Words world, then Memorise for the short surahs', () => {
    expect(top(BILAL)).toEqual(['words', 'mem', 'prayer'])
  })

  it('puts the spoken dialect first for someone who came to speak', () => {
    expect(top(OMAR)).toEqual(['colloq', 'basics', 'words'])
  })

  it('does not push a Hanafi book first on a Shafiʿi student of the sciences', () => {
    expect(top(FATIMA)).toEqual(['aqidah', 'hadith', 'nahw'])
    const fiqh = recommend(readPlan(FATIMA), [], NOW).find((one) => one.place.id === 'fiqh')
    expect(fiqh.why.lowered).toBe(true)
    expect(top({ ...FATIMA, school: 'hanafi' }, [], 1)).toEqual(['fiqh'])
  })
})

describe('recommend: said, then done', () => {
  it('says why: the goal served, the level fitting, nothing practised yet', () => {
    const [first] = recommend(readPlan(OMAR), [], NOW)
    expect(first.why).toEqual({ goal: 'speak', level: true, done: false, lowered: false })
  })

  it('halves what was said once fade-at answers are in', () => {
    const said = recommend(readPlan(OMAR), [], NOW)[0]
    const later = recommend(readPlan(OMAR), [row('nahw-unknown', RANK['fade-at'], 20, 40)], NOW)[0]
    expect(later.parts.goal).toBeCloseTo(said.parts.goal / 2)
  })

  it('lets real practice take over: a speaker drilling Qur’an words every day gets Words first', () => {
    expect(top(OMAR, [row('quiz', 40, 30, 0)], 1)).toEqual(['words'])
    expect(recommend(readPlan(OMAR), [row('quiz', 40, 30, 0)], NOW)[0].why.done).toBe(true)
  })

  it('counts a tab’s own records toward it', () => {
    const colloq = recommend(readPlan(BILAL), [row('words', 12, 10, 0)], NOW).find((one) => one.place.id === 'colloq')
    expect(colloq.parts.done).toBeGreaterThan(0)
  })

  it('with nothing said and nothing done, offers only the first steps', () => {
    expect(top({}, [], 5)).toEqual(['basics', 'words'])
  })
})
