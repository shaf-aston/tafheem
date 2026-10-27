// @vitest-environment happy-dom
import { describe, expect, it } from 'vitest'
import { renderHook } from '@testing-library/react'

import { claimed, slideWay, swipeOf, useSlide } from './useSwipe'

describe('swipeOf', () => {
  it('goes next on a swipe left and back on a swipe right', () => {
    expect(swipeOf({ dx: -100, dy: 5 })).toBe(1)
    expect(swipeOf({ dx: 100, dy: 5 })).toBe(-1)
  })

  it('ignores a short drag and a mostly vertical one', () => {
    expect(swipeOf({ dx: -30, dy: 0 })).toBe(0)
    expect(swipeOf({ dx: -100, dy: 80 })).toBe(0)
  })

  it('takes a quick mouse flick but leaves a slow mouse drag to text selection', () => {
    expect(swipeOf({ dx: -100, dy: 0, ms: 150, mouse: true })).toBe(1)
    expect(swipeOf({ dx: -100, dy: 0, ms: 600, mouse: true })).toBe(0)
    expect(swipeOf({ dx: -100, dy: 0, ms: 600 })).toBe(1)
  })
})

describe('claimed', () => {
  const page = document.createElement('div')
  const gap = document.createElement('input')
  page.append(gap)

  it('leaves a text box to a mouse, but lets a finger start a swipe on one', () => {
    expect(claimed(gap, page)).toBe(true)
    expect(claimed(gap, page, { textBoxes: false })).toBe(false)
  })

  it('leaves a sideways scroller to every pointer', () => {
    const strip = document.createElement('div')
    strip.style.overflowX = 'auto'
    Object.defineProperty(strip, 'scrollWidth', { value: 500 })
    Object.defineProperty(strip, 'clientWidth', { value: 100 })
    const inner = document.createElement('span')
    strip.append(inner)
    page.append(strip)
    document.body.append(page)
    expect(claimed(inner, page, { textBoxes: false })).toBe(true)
  })
})

describe('slideWay', () => {
  it('comes in from the side stepped to, and stays still without a step', () => {
    expect(slideWay(3, 4)).toBe('slide-next')
    expect(slideWay(4, 2)).toBe('slide-prev')
    expect(slideWay(2, 2)).toBe('')
  })
})

describe('useSlide', () => {
  it('slides on a step, but not while held still (a link finding its page)', () => {
    const { result, rerender } = renderHook(({ at, still }) => useSlide(at, still), { initialProps: { at: 0, still: true } })
    rerender({ at: 3, still: true })
    expect(result.current.className).toBe('')
    rerender({ at: 4, still: false })
    expect(result.current.className).toBe('slide-next')
  })
})
