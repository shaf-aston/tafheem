// @vitest-environment happy-dom
import { describe, expect, it } from 'vitest'
import { render } from '@testing-library/react'

import Medal, { CONFETTI } from './Celebration'

describe('Medal', () => {
  it('draws the rays, the sprout and every piece of confetti, hidden from screen readers', () => {
    const { container } = render(<Medal />)
    const medal = container.querySelector('.grow-medal')
    expect(medal.getAttribute('aria-hidden')).toBe('true')
    expect(medal.querySelector('.grow-sprout')).not.toBeNull()
    expect(medal.querySelectorAll('.grow-confetti i')).toHaveLength(CONFETTI.length)
    expect(medal.querySelectorAll(':scope > i')).toHaveLength(12)
  })
})
