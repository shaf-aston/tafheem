import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import PROFILE from '../../config/profile.json'
import { api } from '../../api'
import { forgetRecords, keepRecord, lastRecord, withWaiting } from './lastRecord'
import { hold } from './outbox'
import { fetchSummary } from './progress'
import { profileHeaders } from './profile'

// A device's storage, as a Map: the tests run with no browser.
function memory() {
  const data = new Map()
  return {
    getItem: (k) => data.get(k) ?? null,
    setItem: (k, v) => data.set(k, String(v)),
    removeItem: (k) => data.delete(k),
    key: (i) => [...data.keys()][i] ?? null,
    get length() { return data.size },
  }
}

const row = (item, more = {}) => ({ item, attempts: 1, wrong: 0, avgMs: 900, due: false, known: false, dueAt: '2026-11-20T00:00:00Z', words: [], ...more })
const answer = (item, correct = true, module = 'basics') => ({ body: { module, item, correct }, headers: { who: 'me' } })
const ME = JSON.stringify({ who: 'me' })

beforeEach(() => {
  vi.stubGlobal('localStorage', memory())
  vi.stubGlobal('crypto', { getRandomValues: (bytes) => bytes.fill(7) })
})
afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('counting the waiting answers in', () => {
  it('adds a new item as seen, not yet due or known', () => {
    const rows = withWaiting([], 'basics', [answer('ب')], ME)
    expect(rows).toEqual([expect.objectContaining({ item: 'ب', attempts: 1, wrong: 0, due: false, known: false })])
  })

  it('adds to an item already there, wrong answers too', () => {
    const rows = withWaiting([row('ب', { attempts: 3, wrong: 1, known: true })], 'basics', [answer('ب', false)], ME)
    expect(rows).toEqual([expect.objectContaining({ item: 'ب', attempts: 4, wrong: 2, known: true })])
  })

  it("leaves out another module's answers and another person's", () => {
    const other = { ...answer('ت'), headers: { who: 'someone else' } }
    expect(withWaiting([], 'basics', [answer('ب', true, 'quiz'), other], ME)).toEqual([])
  })

  it('never changes the rows it was given', () => {
    const rows = [row('ب')]
    withWaiting(rows, 'basics', [answer('ب')], ME)
    expect(rows[0].attempts).toBe(1)
  })
})

describe('the copy kept on the device', () => {
  it('comes back as kept, with the waiting answers counted in', () => {
    keepRecord('basics', [row('ب')])
    hold({ module: 'basics', item: 'ت', correct: true }, profileHeaders())
    expect(lastRecord('basics').map((one) => one.item)).toEqual(['ب', 'ت'])
  })

  it('is none when nothing was kept, or the copy is spoiled', () => {
    expect(lastRecord('basics')).toBeNull()
    keepRecord('basics', [row('ب')])
    for (let i = 0; i < localStorage.length; i += 1) localStorage.setItem(localStorage.key(i), '{nope')
    expect(lastRecord('basics')).toBeNull()
  })

  it('is not kept when too big for the device', () => {
    keepRecord('basics', [row('x'.repeat(PROFILE.lastRecord.maxBytes))])
    expect(lastRecord('basics')).toBeNull()
  })

  it('is forgotten for Start over', () => {
    keepRecord('basics', [row('ب')])
    forgetRecords()
    expect(lastRecord('basics')).toBeNull()
  })
})

describe('reading the record', () => {
  it('keeps what the server gave, and gives the copy back when there is no signal', async () => {
    vi.spyOn(api, 'get').mockResolvedValueOnce({ data: { items: [row('ب')] } })
    await fetchSummary('basics')
    vi.spyOn(api, 'get').mockRejectedValue(new Error('Network Error'))
    await expect(fetchSummary('basics')).resolves.toEqual([row('ب')])
  })

  it('still throws when the server refuses, or no copy was kept', async () => {
    keepRecord('basics', [row('ب')])
    vi.spyOn(api, 'get').mockRejectedValue(Object.assign(new Error('refused'), { response: { status: 403 } }))
    await expect(fetchSummary('basics')).rejects.toThrow('refused')
    vi.spyOn(api, 'get').mockRejectedValue(new Error('Network Error'))
    await expect(fetchSummary('quiz')).rejects.toThrow('Network Error')
  })
})
