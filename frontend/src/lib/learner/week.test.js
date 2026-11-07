import process from 'node:process'
import { afterEach, describe, expect, it } from 'vitest'

import { dayKey, weekOf } from './week'

// Thursday 5 November 2026, mid-morning on the learner's own clock.
const NOW = new Date(2026, 10, 5, 10)
const at = (day, hour = 12) => new Date(2026, 10, day, hour).toISOString()
const states = (overview, now = NOW) => weekOf(overview, now).map((day) => day.state)

describe('weekOf', () => {
  it('runs Monday to Sunday of the week holding now, marking today', () => {
    const week = weekOf({ streak: 0, modules: [] }, NOW)
    expect(week.map((day) => dayKey(day.date))).toEqual(
      ['2026-11-02', '2026-11-03', '2026-11-04', '2026-11-05', '2026-11-06', '2026-11-07', '2026-11-08'])
    expect(week.map((day) => day.today)).toEqual([false, false, false, true, false, false, false])
  })

  it('is a week of rest with nothing ever answered', () => {
    expect(states({ streak: 0, modules: [] })).toEqual(['rest', 'rest', 'rest', 'ahead', 'ahead', 'ahead', 'ahead'])
  })

  it('fills the streak back from today once today is answered in', () => {
    const overview = { streak: 3, modules: [{ lastAt: at(5) }] }
    expect(states(overview)).toEqual(['rest', 'studied', 'studied', 'studied', 'ahead', 'ahead', 'ahead'])
  })

  it('fills it back from yesterday while today is still to come', () => {
    const overview = { streak: 2, modules: [{ lastAt: at(4) }] }
    expect(states(overview)).toEqual(['rest', 'studied', 'studied', 'ahead', 'ahead', 'ahead', 'ahead'])
  })

  it('leaves unknown a day before the break the record cannot speak for, and fills one a module last answered', () => {
    // Today and yesterday in a row, Tuesday broke it; one module's last answer was Monday.
    const overview = { streak: 2, modules: [{ lastAt: at(5) }, { lastAt: at(2) }] }
    expect(states(overview)).toEqual(['studied', 'rest', 'studied', 'studied', 'ahead', 'ahead', 'ahead'])
    const gap = { streak: 1, modules: [{ lastAt: at(5) }] }
    expect(states(gap)).toEqual(['unknown', 'unknown', 'rest', 'studied', 'ahead', 'ahead', 'ahead'])
  })

  it('shows rest after the last answer of all', () => {
    expect(states({ streak: 0, modules: [{ lastAt: at(2) }] }))
      .toEqual(['studied', 'rest', 'rest', 'ahead', 'ahead', 'ahead', 'ahead'])
  })

  it('starts a Sunday in the week before, not the one after', () => {
    const sunday = new Date(2026, 10, 8, 9)
    expect(dayKey(weekOf({ streak: 0, modules: [] }, sunday)[0].date)).toBe('2026-11-02')
  })
})

describe('local days', () => {
  const zone = process.env.TZ
  afterEach(() => { process.env.TZ = zone })

  it('files an answer under the learner’s day, not UTC’s', () => {
    process.env.TZ = 'America/Los_Angeles'
    // 03:00 UTC on Thursday is still Wednesday evening in Los Angeles.
    const now = new Date('2026-11-05T18:00:00Z')
    const overview = { streak: 1, modules: [{ lastAt: '2026-11-05T03:00:00+00:00' }] }
    expect(dayKey(new Date(overview.modules[0].lastAt))).toBe('2026-11-04')
    expect(states(overview, now)).toEqual(['unknown', 'rest', 'studied', 'ahead', 'ahead', 'ahead', 'ahead'])
  })

  it('counts seven days across a clock change', () => {
    process.env.TZ = 'Europe/London'
    // British Summer Time ends on Sunday 25 October 2026.
    const week = weekOf({ streak: 0, modules: [] }, new Date(2026, 9, 25, 12))
    expect(week.map((day) => dayKey(day.date))).toEqual(
      ['2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22', '2026-10-23', '2026-10-24', '2026-10-25'])
  })
})
