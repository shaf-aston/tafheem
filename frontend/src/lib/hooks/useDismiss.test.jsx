// @vitest-environment happy-dom
import { cleanup, fireEvent, render } from '@testing-library/react'
import { useRef } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { useDismiss } from './useDismiss'

function Box({ onDismiss, options }) {
  const ref = useRef(null)
  useDismiss(ref, onDismiss, options)
  return (
    <div>
      <div ref={ref} data-testid="in"><button>inside</button></div>
      <button>outside</button>
    </div>
  )
}
const press = (el) => fireEvent.pointerDown(el)

afterEach(cleanup)

describe('useDismiss', () => {
  it('closes on Escape and on a press outside, not on a press inside', () => {
    const onDismiss = vi.fn()
    const { getByText } = render(<Box onDismiss={onDismiss} />)
    press(getByText('inside'))
    expect(onDismiss).not.toHaveBeenCalled()
    press(getByText('outside'))
    fireEvent.keyDown(document, { key: 'Escape' })
    fireEvent.keyDown(document, { key: 'a' })
    expect(onDismiss).toHaveBeenCalledTimes(2)
  })

  it('listens only to what it is asked to, and only while enabled', () => {
    const onDismiss = vi.fn()
    const { getByText, rerender } = render(<Box onDismiss={onDismiss} options={{ escape: false }} />)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onDismiss).not.toHaveBeenCalled()
    rerender(<Box onDismiss={onDismiss} options={{ outside: false }} />)
    press(getByText('outside'))
    expect(onDismiss).not.toHaveBeenCalled()
    rerender(<Box onDismiss={onDismiss} options={{ enabled: false }} />)
    press(getByText('outside'))
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onDismiss).not.toHaveBeenCalled()
  })

  it('stops listening when the component goes', () => {
    const onDismiss = vi.fn()
    const { unmount } = render(<Box onDismiss={onDismiss} />)
    unmount()
    press(document.body)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onDismiss).not.toHaveBeenCalled()
  })
})
