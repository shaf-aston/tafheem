import { afterEach, describe, expect, it, vi } from 'vitest'

import { readRouteFromUrl, readTabFromUrl, readViewParam, writeTabToUrl, writeViewParams } from './tabUrl'

// The registry's shape, with Nahw deliberately not first, so a legacy link
// landing on "the first tab" and one landing on Nahw cannot be mistaken.
const TABS = [{ id: 'quran' }, { id: 'nahw' }, { id: 'dict' }]

// Just enough of a browser for the address: where we are, and the two ways of
// writing a history entry, spied on so a test can say which one ran.
function browserAt(search, state = { step: 4 }) {
  const location = { href: `https://tafheem.test/app${search}`, search }
  const history = { state, pushState: vi.fn(), replaceState: vi.fn() }
  vi.stubGlobal('window', { location, history })
  return history
}
afterEach(() => vi.unstubAllGlobals())

/** The address a history write was handed, as its query only. */
const written = (spy) => new URL(String(spy.mock.calls[0][2])).searchParams

describe('which tab the address asks for', () => {
  it('sends the two old tabs to the one they became', () => {
    for (const old of ['iraab', 'tarkeeb']) {
      browserAt(`?tab=${old}`)
      expect(readTabFromUrl(TABS)).toBe('nahw')
    }
  })

  it('opens the first tab for a tab it does not know, or none at all', () => {
    for (const search of ['?tab=gone', '', '?tab=']) {
      browserAt(search)
      expect(readTabFromUrl(TABS), search).toBe('quran')
    }
  })

  it('opens a known tab as itself', () => {
    browserAt('?tab=dict')
    expect(readTabFromUrl(TABS)).toBe('dict')
  })
})

describe('the place the address names', () => {
  it('names no tab when the address has none, even with a word on it', () => {
    browserAt('?q=كتب')
    expect(readRouteFromUrl(TABS)).toEqual({ tab: null, value: 'كتب' })
  })

  it('reads an empty word as no word', () => {
    browserAt('?tab=dict&q=')
    expect(readRouteFromUrl(TABS)).toEqual({ tab: 'dict', value: null })
  })

  it('reads tab and word together', () => {
    browserAt('?tab=quran&q=2:255')
    expect(readRouteFromUrl(TABS)).toEqual({ tab: 'quran', value: '2:255' })
  })
})

describe('one in-tab choice from the address', () => {
  it('is null when the address does not have it', () => {
    browserAt('?tab=nahw')
    expect(readViewParam('view', ['table', 'tree'])).toBe(null)
  })

  it('is null when the value is not one the tab allows', () => {
    browserAt('?tab=nahw&view=nonsense')
    expect(readViewParam('view', ['table', 'tree'])).toBe(null)
  })

  it('is the value when it is allowed', () => {
    browserAt('?tab=nahw&view=tree')
    expect(readViewParam('view', ['table', 'tree'])).toBe('tree')
  })

  it('takes any value when no list of allowed ones is given', () => {
    browserAt('?tab=nahw&topic=anything-at-all')
    expect(readViewParam('topic')).toBe('anything-at-all')
    expect(readViewParam('topic', null)).toBe('anything-at-all')
  })
})

describe('writing a place into the address', () => {
  it('replaces the current entry when asked, and pushes no new one', () => {
    const history = browserAt('?tab=dict')
    writeTabToUrl('dict', 'كتب', { replace: true, state: { step: 2 } })
    expect(history.replaceState).toHaveBeenCalledTimes(1)
    expect(history.pushState).not.toHaveBeenCalled()
    expect(history.replaceState.mock.calls[0][0]).toEqual({ step: 2 })
  })

  it('pushes a new entry by default, carrying the state it was given', () => {
    const history = browserAt('?tab=dict')
    writeTabToUrl('quran', '1:1', { state: { step: 7 } })
    expect(history.pushState).toHaveBeenCalledTimes(1)
    expect(history.replaceState).not.toHaveBeenCalled()
    expect(history.pushState.mock.calls[0][0]).toEqual({ step: 7 })
    expect(written(history.pushState).get('tab')).toBe('quran')
    expect(written(history.pushState).get('q')).toBe('1:1')
  })

  const CHOICES = 'view=tree&mode=a&topic=b&kind=c&show=d&question=e'

  it('drops every in-tab choice when the tab changes, and keeps anything else', () => {
    const history = browserAt(`?tab=nahw&${CHOICES}&lang=ur`)
    writeTabToUrl('dict', 'كتب')
    const params = written(history.pushState)
    for (const key of ['view', 'mode', 'topic', 'kind', 'show', 'question']) expect(params.has(key), key).toBe(false)
    expect(params.get('lang')).toBe('ur')
    expect(params.get('tab')).toBe('dict')
  })

  it('keeps the in-tab choices when the tab stays the same', () => {
    const history = browserAt(`?tab=nahw&${CHOICES}`)
    writeTabToUrl('nahw', '1:1')
    const params = written(history.pushState)
    expect(params.get('view')).toBe('tree')
    expect(params.get('question')).toBe('e')
    expect(params.get('q')).toBe('1:1')
  })

  it('takes the word off the address when there is none', () => {
    const history = browserAt('?tab=dict&q=كتب')
    writeTabToUrl('dict', null)
    expect(written(history.pushState).has('q')).toBe(false)
  })
})

describe('writing in-tab choices into the address', () => {
  it('removes a choice set to nothing, sets one given, and keeps the entry\'s state', () => {
    const state = { step: 3 }
    const history = browserAt('?tab=nahw&view=tree&topic=a', state)
    writeViewParams({ view: '', topic: null, mode: 'b' })
    expect(history.pushState).not.toHaveBeenCalled()
    expect(history.replaceState).toHaveBeenCalledTimes(1)
    expect(history.replaceState.mock.calls[0][0]).toBe(state)
    const params = written(history.replaceState)
    expect(params.has('view')).toBe(false)
    expect(params.has('topic')).toBe(false)
    expect(params.get('mode')).toBe('b')
    expect(params.get('tab')).toBe('nahw')
  })
})
