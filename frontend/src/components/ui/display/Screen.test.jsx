// @vitest-environment happy-dom
import { fireEvent, render } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Screen from './Screen'

const shown = (container) => container.firstChild

describe('Screen', () => {
  beforeEach(() => { globalThis.scrollTo = vi.fn() })

  it('opens at the top and adds no fade of its own on first show (the tab fades)', () => {
    const { container } = render(<Screen id="a" depth={0}>one</Screen>)
    expect(globalThis.scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'instant' })
    expect(shown(container).className).toBe('screen')
  })

  it('a step to another screen opens at the top and fades once, then drops the fade', () => {
    const { container, rerender } = render(<Screen id="a" depth={0}>one</Screen>)
    globalThis.scrollTo.mockClear()
    rerender(<Screen id="b" depth={1}>two</Screen>)
    expect(globalThis.scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'instant' })
    expect(shown(container).className).toBe('screen fade-in')
    // A move inside it bubbles up and is not its own.
    const inner = document.createElement('span')
    shown(container).append(inner)
    fireEvent.animationEnd(inner)
    expect(shown(container).className).toBe('screen fade-in')
    fireEvent.animationEnd(shown(container))
    expect(shown(container).className).toBe('screen')
  })
})
