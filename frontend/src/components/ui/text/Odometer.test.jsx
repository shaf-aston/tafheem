// @vitest-environment happy-dom
import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import Odometer from './Odometer'

describe('Odometer', () => {
  it('says the number once, and draws each digit as a column slid to its value', () => {
    const { container } = render(<Odometer value={407} />)
    expect(container.querySelector('.sr-only').textContent).toBe('407')
    const slid = [...container.querySelectorAll('.odometer-digit > span')].map((col) => col.style.getPropertyValue('--d'))
    expect(slid).toEqual(['4', '0', '7'])
  })
})
