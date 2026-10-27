// @vitest-environment happy-dom
// A search that could not run: announced, explained, and retryable; never mistaken for an empty result.
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import ErrorAlert from './ErrorAlert'

afterEach(cleanup)

describe('ErrorAlert', () => {
  it('is announced as an alert, with the server message in words', () => {
    render(<ErrorAlert title="Lookup failed" error={{ response: { status: 429 } }} />)
    const alert = screen.getByRole('alert')
    expect(alert.textContent).toContain('Lookup failed')
    expect(alert.textContent).toContain('Too many requests')
  })

  it('offers a retry only when given one, and it calls back', () => {
    render(<ErrorAlert error={{ message: 'x' }} />)
    expect(screen.queryByRole('button')).toBeNull()
    cleanup()
    const onRetry = vi.fn()
    render(<ErrorAlert error={{ message: 'x' }} onRetry={onRetry} />)
    fireEvent.click(screen.getByRole('button'))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })
})
