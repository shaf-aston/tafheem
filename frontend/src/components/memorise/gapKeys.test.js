// @vitest-environment happy-dom
import { describe, expect, it, vi } from 'vitest'

import { nextGapOnEnter } from './gapKeys'

vi.mock('../../lib/motion/scrollToEl', () => ({ scrollToEl: vi.fn() }))

const page = () => {
  const root = document.createElement('div')
  root.innerHTML = '<input data-gap><input data-gap><input id="other">'
  document.body.append(root)
  return { root, gaps: [...root.querySelectorAll('[data-gap]')], other: root.querySelector('#other') }
}
const press = (root, target, key = 'Enter', extra = {}) => {
  const event = { key, target, currentTarget: root, preventDefault: vi.fn(), nativeEvent: {}, ...extra }
  nextGapOnEnter(event)
  return event
}

describe('nextGapOnEnter', () => {
  it('moves from a gap to the next one', () => {
    const { root, gaps } = page()
    gaps[0].focus()
    expect(press(root, gaps[0]).preventDefault).toHaveBeenCalled()
    expect(document.activeElement).toBe(gaps[1])
  })

  it('puts the keyboard away after the last gap', () => {
    const { root, gaps } = page()
    gaps[1].focus()
    press(root, gaps[1])
    expect(document.activeElement).not.toBe(gaps[1])
  })

  it('leaves other keys, other boxes and a word still being composed alone', () => {
    const { root, gaps, other } = page()
    gaps[0].focus()
    expect(press(root, gaps[0], 'a').preventDefault).not.toHaveBeenCalled()
    expect(press(root, other).preventDefault).not.toHaveBeenCalled()
    expect(press(root, gaps[0], 'Enter', { nativeEvent: { isComposing: true } }).preventDefault).not.toHaveBeenCalled()
    expect(document.activeElement).toBe(gaps[0])
  })
})
