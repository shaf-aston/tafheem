import { afterEach, describe, expect, it } from 'vitest'

import { readRouteFromUrl, readViewParam, shareLink, writeTabToUrl, writeViewParams } from './tabUrl'

const TABS = [{ id: 'nahw' }, { id: 'dict' }, { id: 'mem' }]
const ORIGIN = 'https://tafheem-app.vercel.app'

// A browser tab reduced to what tabUrl touches: the address and one history entry's state.
function openAt(path, state = null) {
  const page = { href: ORIGIN + path, state }
  const move = (next, _title, url) => { page.state = next; page.href = new URL(url, page.href).href }
  globalThis.window = {
    location: { get href() { return page.href }, get pathname() { return new URL(page.href).pathname }, origin: ORIGIN },
    history: { get state() { return page.state }, pushState: move, replaceState: move },
  }
  return page
}
const shown = (page) => page.href.slice(ORIGIN.length)

afterEach(() => { delete globalThis.window })

describe('the address shows only the tab', () => {
  it('an old link opens its word and view, then the address is tidied and a reload keeps both', () => {
    const page = openAt('/app?tab=nahw&q=%D8%B0%D9%87%D8%A8&view=analyse')
    expect(readRouteFromUrl(TABS)).toEqual({ tab: 'nahw', value: 'ذهب' })
    writeTabToUrl('nahw', 'ذهب', { replace: true, state: { step: 0 } })
    expect(shown(page)).toBe('/app/nahw')
    // A reload keeps the address and the entry's state, nothing else.
    openAt(shown(page), page.state)
    expect(readRouteFromUrl(TABS)).toEqual({ tab: 'nahw', value: 'ذهب' })
    expect(readViewParam('view', ['analyse', 'tree'])).toBe('analyse')
  })

  it('a word searched is a new back step with a clean address', () => {
    const page = openAt('/app/dict', { step: 0, value: null, view: {} })
    writeTabToUrl('dict', 'كتب', { state: { step: 1 } })
    expect(shown(page)).toBe('/app/dict')
    expect(page.state).toEqual({ step: 1, value: 'كتب', view: {} })
  })

  it('choices inside a tab stay with that tab and are dropped on leaving it', () => {
    const page = openAt('/app/mem', { step: 0, value: null, view: {} })
    writeViewParams({ mode: 'recite' })
    expect(shown(page)).toBe('/app/mem')
    writeTabToUrl('mem', '1:1', { state: { step: 1 } })
    expect(readViewParam('mode')).toBe('recite')
    writeTabToUrl('dict', null, { state: { step: 2 } })
    expect(readViewParam('mode')).toBe(null)
    writeViewParams({ mode: 'recite' })
    writeViewParams({ mode: '' })
    expect(readViewParam('mode')).toBe(null)
  })

  it('Copy link writes the place out, and that link opens the same place', () => {
    openAt('/app/nahw', { step: 3, value: 'ذهب الولد', view: { view: 'tree' } })
    const link = shareLink()
    expect(link).toBe(`${ORIGIN}/app/nahw?q=${encodeURIComponent('ذهب الولد').replace(/%20/g, '+')}&view=tree`)
    openAt(link.slice(ORIGIN.length))
    expect(readRouteFromUrl(TABS)).toEqual({ tab: 'nahw', value: 'ذهب الولد' })
    expect(readViewParam('view')).toBe('tree')
  })

  it('old tab names, unknown tabs and the bare app', () => {
    openAt('/app?tab=iraab&q=x')
    expect(readRouteFromUrl(TABS)).toEqual({ tab: 'nahw', value: 'x' })
    openAt('/app/nowhere')
    expect(readRouteFromUrl(TABS)).toEqual({ tab: 'nahw', value: null })
    openAt('/app')
    expect(readRouteFromUrl(TABS)).toEqual({ tab: null, value: null })
  })

  it('back onto an entry written before the tidy-up still reads its query', () => {
    openAt('/app?tab=dict&q=%D9%83%D8%AA%D8%A8&view=lane', { step: 2 })
    expect(readRouteFromUrl(TABS)).toEqual({ tab: 'dict', value: 'كتب' })
    expect(readViewParam('view')).toBe('lane')
  })
})
