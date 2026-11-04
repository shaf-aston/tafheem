// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from 'vitest'

import { keepInSight } from './scrollToEl'

const at = (top, height = 40) => {
  const el = document.createElement('span')
  el.getBoundingClientRect = () => ({ top, bottom: top + height })
  return el
}

afterEach(() => {
  vi.restoreAllMocks()
  document.documentElement.style.removeProperty('--app-header-h')
})

describe('keepInSight', () => {
  it('leaves the page still while the word is between the header and the dock', () => {
    const scroll = vi.spyOn(globalThis, 'scrollTo').mockImplementation(() => {})
    document.documentElement.style.setProperty('--app-header-h', '64px')
    keepInSight(at(300), 600)
    expect(scroll).not.toHaveBeenCalled()
  })

  it('brings a word under the dock up to a third of the way down the clear band', () => {
    const scroll = vi.spyOn(globalThis, 'scrollTo').mockImplementation(() => {})
    document.documentElement.style.setProperty('--app-header-h', '64px')
    keepInSight(at(640), 664)
    // band 64..664, a third down is 264: the word at 640 (its foot under the dock) moves up by 376
    expect(scroll.mock.calls[0][0].top).toBe(globalThis.scrollY + 376)
  })

  it('brings back a word hidden under the header', () => {
    const scroll = vi.spyOn(globalThis, 'scrollTo').mockImplementation(() => {})
    document.documentElement.style.setProperty('--app-header-h', '64px')
    keepInSight(at(20), 664)
    expect(scroll.mock.calls[0][0].top).toBe(globalThis.scrollY - 244)
  })

  it('does nothing with no word', () => {
    const scroll = vi.spyOn(globalThis, 'scrollTo').mockImplementation(() => {})
    keepInSight(null)
    expect(scroll).not.toHaveBeenCalled()
  })
})
