// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'

import ZoomBar from './ZoomBar'

afterEach(cleanup)

const knobs = { min: 0.5, max: 3, step: 0.25 }
const bar = (zoom, on = {}) => {
  const handlers = { onStep: vi.fn(), onSet: vi.fn(), onReset: vi.fn(), ...on }
  render(<ZoomBar zoom={zoom} knobs={knobs} {...handlers} />)
  return handlers
}

describe('ZoomBar', () => {
  it('steps out and in, slides to a level and fits back to 100%', () => {
    const { onStep, onSet, onReset } = bar(1.5)
    fireEvent.click(screen.getByRole('button', { name: 'Zoom out' }))
    fireEvent.click(screen.getByRole('button', { name: 'Zoom in' }))
    expect(onStep.mock.calls).toEqual([[-1], [1]])

    fireEvent.change(screen.getByRole('slider', { name: 'Zoom level' }), { target: { value: '2' } })
    expect(onSet).toHaveBeenCalledWith(2)

    fireEvent.click(screen.getByRole('button', { name: 'Fit' }))
    expect(onReset).toHaveBeenCalled()
    expect(screen.getByText('150%')).toBeTruthy()
  })

  it('turns a step off where there is no further, and Fit where it is already fitted', () => {
    bar(1)
    expect(screen.getByRole('button', { name: 'Fit' }).disabled).toBe(true)
    cleanup()
    bar(3)
    expect(screen.getByRole('button', { name: 'Zoom in' }).disabled).toBe(true)
    cleanup()
    bar(0.5)
    expect(screen.getByRole('button', { name: 'Zoom out' }).disabled).toBe(true)
  })
})
