// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'

import PlaceStrip from './PlaceStrip'

afterEach(cleanup)

describe('PlaceStrip', () => {
  it('shows every place at once, marks the open one and the star count, and picks on a tap', () => {
    const rijal = vi.fn()
    const items = [
      { label: 'Starred', hint: 'hadith you kept', count: 3, on: false, pick: vi.fn() },
      { label: 'Rijal', hint: 'who passed them on', on: true, pick: rijal },
      { label: 'Scholars', hint: 'what they said of them', on: false, pick: vi.fn() },
      { label: 'Terms', hint: 'the words of the science', on: false, pick: vi.fn() },
    ]
    render(<PlaceStrip accent="#0a0" items={items} />)

    expect(screen.getAllByRole('button').map((b) => b.textContent)).toEqual(['Starred3', 'Rijal', 'Scholars', 'Terms'])
    expect(screen.getByRole('button', { name: 'Rijal' }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByRole('button', { name: 'Terms' }).getAttribute('aria-pressed')).toBe('false')

    fireEvent.click(screen.getByRole('button', { name: 'Rijal' }))
    expect(rijal).toHaveBeenCalledOnce()
  })
})
