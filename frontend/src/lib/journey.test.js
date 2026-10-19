import { afterEach, describe, expect, it, vi } from 'vitest'

import { jumpTabs, lastOn, nearest, resume, resumePlace, tabNow, trailFor } from './journey'

const STEPS = [
  { tab: 'dict', value: null },
  { tab: 'dict', value: 'كتب' },
  { tab: 'quran', value: '2:255' },
  { tab: 'dict', value: 'book' },
  { tab: 'dict', value: 'سطر' },
]

describe('trailFor', () => {
  it('keeps this tab, in the order walked', () => {
    expect(trailFor(STEPS, 'dict').map((s) => s.value)).toEqual(['كتب', 'book', 'سطر'])
  })

  it('keeps the steps ahead after a step back, they are one click away', () => {
    expect(trailFor(STEPS, 'dict').map((s) => s.index)).toEqual([1, 3, 4])
  })

  it('drops a tab opened with nothing, there is no word to go back to', () => {
    expect(trailFor([STEPS[0]], 'dict')).toEqual([])
  })

  it('carries the index, which is what a click jumps to', () => {
    expect(trailFor(STEPS, 'quran')).toEqual([{ tab: 'quran', value: '2:255', index: 2 }])
  })

  // Dictionary on فهم, a glance at Daleel, back to Dictionary reopened on فهم.
  const RETURN = [
    { tab: 'dict', value: 'فهم' }, { tab: 'daleel', value: null }, { tab: 'dict', value: 'فهم' },
  ]

  it('draws a return to the same word once, as the later step', () => {
    expect(trailFor(RETURN, 'dict', 2).map((s) => s.index)).toEqual([2])
  })

  it('but keeps the earlier one when that is where we are', () => {
    expect(trailFor(RETURN, 'dict', 0).map((s) => s.index)).toEqual([0])
  })
})

describe('nearest', () => {
  // Six words looked up in a row, so the line has to drop some.
  const many = ['a', 'b', 'c', 'd', 'e', 'f'].map((value, index) => ({ tab: 'dict', value, index }))

  it('leaves a short trail alone', () => {
    expect(nearest(many.slice(0, 3), 2, 5)).toEqual({ shown: many.slice(0, 3), sliced: false })
  })

  it('drops the oldest, keeps where we are', () => {
    const { shown, sliced } = nearest(many, 5, 5)
    expect(shown.map((s) => s.value)).toEqual(['b', 'c', 'd', 'e', 'f'])
    expect(sliced).toBe(true)
  })

  it('keeps one step of what is ahead in view', () => {
    expect(nearest(many, 2, 5).shown.map((s) => s.value)).toEqual(['a', 'b', 'c', 'd', 'e'])
  })

  it('never starts before the beginning', () => {
    expect(nearest(many, 0, 5).shown.map((s) => s.value)).toEqual(['a', 'b', 'c', 'd', 'e'])
  })
})

describe('resume', () => {
  const saved = { steps: STEPS, at: 4 }

  it('starts at the address when nothing was saved', () => {
    expect(resume(null, STEPS[1], undefined)).toEqual({ steps: [STEPS[1]], at: 0 })
  })

  it('a reload sits where it was, path intact', () => {
    expect(resume(saved, STEPS[4], 4)).toEqual({ steps: STEPS, at: 4 })
  })

  it('a back press across a reload lands on the step the browser names', () => {
    expect(resume(saved, STEPS[3], 3)).toEqual({ steps: STEPS, at: 3 })
  })

  it('trusts the saved index when the browser has no usable state', () => {
    expect(resume(saved, STEPS[4], undefined)).toEqual({ steps: STEPS, at: 4 })
  })

  it('ignores a state index that does not match the address', () => {
    expect(resume(saved, STEPS[4], 1)).toEqual({ steps: STEPS, at: 4 })
  })

  it('a bare address opens on the last word of that tab, like a bookmark', () => {
    expect(resume(saved, { tab: 'dict', value: null }, undefined)).toEqual({ steps: STEPS, at: 4 })
    expect(resume({ steps: STEPS, at: 3 }, { tab: 'quran', value: null }, undefined))
      .toEqual({ steps: [...STEPS.slice(0, 4), { tab: 'quran', value: '2:255' }], at: 4 })
  })

  it('a bare address on a tab never reached opens blank', () => {
    expect(resume(saved, { tab: 'sarf', value: null }, undefined))
      .toEqual({ steps: [...STEPS, { tab: 'sarf', value: null }], at: 5 })
  })

  it('a pasted link is a new step after the current one, ahead dropped', () => {
    const link = { tab: 'daleel', value: 'patience' }
    expect(resume({ steps: STEPS, at: 2 }, link, undefined))
      .toEqual({ steps: [...STEPS.slice(0, 3), link], at: 3 })
  })

  it('a place on a tab opened with nothing fills that step in, not one after it', () => {
    const blank = [STEPS[0], { tab: 'mem', value: null }]
    const link = { tab: 'mem', value: '2:6' }
    expect(resume({ steps: blank, at: 1 }, link, undefined)).toEqual({ steps: [STEPS[0], link], at: 1 })
  })
})

describe('lastOn', () => {
  it('is the latest word on that tab at or before here', () => {
    expect(lastOn(STEPS, 4, 'dict')).toBe('سطر')
    expect(lastOn(STEPS, 3, 'dict')).toBe('book')
    expect(lastOn(STEPS, 4, 'quran')).toBe('2:255')
  })

  it('does not count steps ahead, and is null for a tab never reached', () => {
    expect(lastOn(STEPS, 1, 'quran')).toBe(null)
    expect(lastOn(STEPS, 4, 'sarf')).toBe(null)
  })

  it('skips a tab opened with nothing', () => {
    expect(lastOn(STEPS, 0, 'dict')).toBe(null)
  })
})

describe('tabNow', () => {
  it('is the tab of the step the browser sits on', () => {
    expect(tabNow(STEPS, 2)).toBe('quran')
  })

  it('is nothing before the first step is recorded', () => {
    expect(tabNow([], -1)).toBe(null)
  })
})

describe('nearest, at the edge of fitting', () => {
  const walk = (n) => Array.from({ length: n }, (_, index) => ({ tab: 'dict', value: `w${index}`, index }))

  it('shows a trail exactly as long as the room whole', () => {
    expect(nearest(walk(3), 2, 3)).toEqual({ shown: walk(3), sliced: false })
  })

  it('slices a trail one longer than the room, and says so', () => {
    const { shown, sliced } = nearest(walk(4), 3, 3)
    expect(shown.map((s) => s.value)).toEqual(['w1', 'w2', 'w3'])
    expect(sliced).toBe(true)
  })
})

// The journey proper, against a browser history kept in memory: entries, the
// one we sit on, and popstate sent when the arrow moves us. The module keeps
// its state between calls, as a page does, so each case loads it fresh.
const JOURNEY_TABS = [{ id: 'dict' }, { id: 'quran' }]

function browserAt(search) {
  const entries = [{ state: null, url: new URL(`https://tafheem.test/app${search}`) }]
  let index = 0
  const popped = []
  const location = {
    get href() { return entries[index].url.href },
    get search() { return entries[index].url.search },
    get pathname() { return entries[index].url.pathname },
    origin: 'https://tafheem.test',
  }
  const pop = () => { for (const listener of popped) listener({ state: entries[index].state }) }
  const history = {
    get state() { return entries[index].state },
    pushState: vi.fn((state, _title, url) => {
      entries.splice(index + 1)
      entries.push({ state, url: new URL(String(url), entries[index].url) })
      index += 1
    }),
    replaceState: vi.fn((state, _title, url) => { entries[index] = { state, url: new URL(String(url), entries[index].url) } }),
    go: vi.fn((delta) => { index += delta; pop() }),
  }
  const addEventListener = vi.fn((type, listener) => { if (type === 'popstate') popped.push(listener) })
  const data = new Map()
  vi.stubGlobal('window', { location, history, addEventListener })
  vi.stubGlobal('history', history)
  vi.stubGlobal('localStorage', {
    getItem: (k) => (data.has(k) ? data.get(k) : null),
    setItem: (k, v) => data.set(k, String(v)),
    removeItem: (k) => data.delete(k),
  })
  return {
    history,
    addEventListener,
    /** The arrow lands on an entry this session did not write, as one from an expired path would be. */
    arrive(state, entrySearch) {
      entries.splice(index + 1)
      entries.push({ state, url: new URL(`https://tafheem.test/app${entrySearch}`) })
      index += 1
      pop()
    },
  }
}

async function freshJourney(search) {
  const browser = browserAt(search)
  vi.resetModules()
  const journey = await import('./journey')
  journey.startJourney(JOURNEY_TABS)
  browser.history.pushState.mockClear()
  browser.history.replaceState.mockClear()
  return { browser, journey }
}

describe('the journey and the back arrow', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('follows the address, not the step number, when the two disagree', async () => {
    const { browser, journey } = await freshJourney('?tab=dict&q=a')
    journey.visit('dict', 'b')
    const jumps = []
    journey.onJump((place) => jumps.push(place))
    // Step 0 of this path is dict:a; the entry the arrow landed on is a Qur'an address.
    browser.arrive({ step: 0 }, '?tab=quran&q=1:1')
    expect(journey.placeNow()).toEqual({ tab: 'quran', value: '1:1' })
    expect(jumps).toEqual([{ tab: 'quran', value: '1:1' }])
    // Walked onto from where we were, and the entry restamped with that step.
    expect(browser.history.state.step).toBe(2)
    expect(journey.lastPlaceOn('dict')).toBe('b')
  })

  it('sits on the step the entry names when it is this address', async () => {
    const { browser, journey } = await freshJourney('?tab=dict&q=a')
    journey.visit('dict', 'b')
    browser.history.go(-1)
    expect(journey.placeNow()).toEqual({ tab: 'dict', value: 'a' })
    expect(browser.history.replaceState).not.toHaveBeenCalled()
  })

  it('listens to the arrow once however many times it is started', async () => {
    const { browser, journey } = await freshJourney('?tab=dict&q=a')
    expect(journey.startJourney(JOURNEY_TABS)).toEqual({ tab: 'dict', value: 'a' })
    expect(browser.addEventListener).toHaveBeenCalledTimes(1)
  })

  it('treats a visit to where we already are as no step, and writes nothing', async () => {
    const { browser, journey } = await freshJourney('?tab=dict&q=a')
    expect(journey.visit('dict', 'a')).toBe(false)
    expect(browser.history.pushState).not.toHaveBeenCalled()
    expect(browser.history.replaceState).not.toHaveBeenCalled()
  })

  it('pushes a new entry for a visit after going back, rather than overwriting', async () => {
    const { browser, journey } = await freshJourney('?tab=dict&q=a')
    journey.visit('dict', 'b')
    browser.history.go(-1)
    browser.history.pushState.mockClear()
    expect(journey.visit('dict', 'c')).toBe(true)
    expect(browser.history.pushState).toHaveBeenCalledTimes(1)
    expect(browser.history.replaceState).not.toHaveBeenCalled()
    expect(browser.history.state.step).toBe(1)
  })

  it('fills in a tab opened with nothing by replacing its entry', async () => {
    const { browser, journey } = await freshJourney('?tab=dict')
    expect(journey.visit('dict', 'a')).toBe(true)
    expect(browser.history.replaceState).toHaveBeenCalledTimes(1)
    expect(browser.history.pushState).not.toHaveBeenCalled()
    expect(browser.history.state.step).toBe(0)
  })

  it('jumps back to a walked step by the distance from here', async () => {
    const { browser, journey } = await freshJourney('?tab=dict&q=a')
    for (const value of ['b', 'c', 'd']) journey.visit('dict', value)
    journey.jumpTo(1)
    expect(browser.history.go).toHaveBeenCalledWith(-2)
    expect(journey.placeNow()).toEqual({ tab: 'dict', value: 'b' })
  })
})

describe('what Home offers', () => {
  const listed = ['home', 'quran', 'nahw', 'sarf', 'dict', 'quiz'].map((id) => ({ id }))
  const base = { listed, fallback: ['quran', 'nahw', 'sarf', 'dict'], home: 'home', count: 3 }

  it('resumes the newest step with a word, never Home', () => {
    const steps = [{ tab: 'dict', value: 'a' }, { tab: 'sarf', value: null }, { tab: 'home', value: 'x' }]
    expect(resumePlace(steps, listed, 'home')).toEqual({ tab: 'dict', value: 'a' })
    expect(resumePlace([], listed, 'home')).toBe(null)
  })

  it('tiles are the recent tabs, newest first, without the resume tab or repeats', () => {
    const steps = [{ tab: 'quiz' }, { tab: 'sarf' }, { tab: 'quiz' }, { tab: 'dict', value: 'a' }]
    expect(jumpTabs(steps, { ...base, skip: 'dict' })).toEqual(['quiz', 'sarf', 'quran'])
  })

  it('a first visit falls back, and a pinned tab stays when offline', () => {
    expect(jumpTabs([], base)).toEqual(['quran', 'nahw', 'sarf'])
    expect(jumpTabs([], { ...base, pin: 'dict' })).toEqual(['quran', 'nahw', 'dict'])
  })
})
