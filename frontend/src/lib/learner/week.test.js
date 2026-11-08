import process from 'node:process'
import { afterEach, describe, expect, it } from 'vitest'

import { dayKey, weekOf } from './week'

// Thursday 5 November 2026, mid-morning on the learner's own clock.
const NOW = new Date(2026, 10, 5, 10)
const states = (days, now = NOW) => weekOf({ days }, now).map((day) => day.state)

describe('weekOf', () => {
  it('runs Monday to Sunday of the week holding now, marking today', () => {
    const week = weekOf({ days: [] }, NOW)
    expect(week.map((day) => dayKey(day.date))).toEqual(
      ['2026-11-02', '2026-11-03', '2026-11-04', '2026-11-05', '2026-11-06', '2026-11-07', '2026-11-08'])
    expect(week.map((day) => day.today)).toEqual([false, false, false, true, false, false, false])
  })

  it('is rest for the days gone by and ahead for the rest, with nothing answered', () => {
    expect(states([])).toEqual(['rest', 'rest', 'rest', 'ahead', 'ahead', 'ahead', 'ahead'])
  })

  it('fills exactly the days the server lists, today included once answered in', () => {
    expect(states(['2026-11-05', '2026-11-03', '2026-10-30']))
      .toEqual(['rest', 'studied', 'rest', 'studied', 'ahead', 'ahead', 'ahead'])
  })

  it('reads an overview from before days were sent as nothing answered, not as an error', () => {
    expect(weekOf({ streak: 2, modules: [] }, NOW).map((day) => day.state)).toEqual(states([]))
  })

  it('starts a Sunday in the week before, not the one after', () => {
    const sunday = new Date(2026, 10, 8, 9)
    expect(dayKey(weekOf({ days: [] }, sunday)[0].date)).toBe('2026-11-02')
  })
})

describe('local days', () => {
  const zone = process.env.TZ
  afterEach(() => { process.env.TZ = zone })

  it('names a day by the learner’s calendar, not UTC’s', () => {
    process.env.TZ = 'America/Los_Angeles'
    // 03:00 UTC on Thursday is still Wednesday evening in Los Angeles.
    expect(dayKey(new Date('2026-11-05T03:00:00+00:00'))).toBe('2026-11-04')
  })

  it('counts seven days across a clock change', () => {
    process.env.TZ = 'Europe/London'
    // British Summer Time ends on Sunday 25 October 2026.
    const week = weekOf({ days: [] }, new Date(2026, 9, 25, 12))
    expect(week.map((day) => dayKey(day.date))).toEqual(
      ['2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22', '2026-10-23', '2026-10-24', '2026-10-25'])
  })
})
