// @vitest-environment happy-dom
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import SpellingKey from './SpellingKey'

let spelling = true
vi.mock('../../../lib/store/settings', () => ({ useSetting: () => spelling }))

afterEach(() => { cleanup(); spelling = true })

describe('SpellingKey', () => {
  it('lists each sound under a fold, letters beside what they stand for', () => {
    render(<SpellingKey keys={{ 3: 'ع', kh: 'خ' }} />)
    expect(screen.getByText('How to read the spelling')).toBeTruthy()
    expect(screen.getByText('3').nextSibling.textContent).toBe('ع')
    expect(screen.getByText('kh').nextSibling.textContent).toBe('خ')
  })

  it('draws nothing for a unit with no key, or while the spelling is off', () => {
    const { container, rerender } = render(<SpellingKey keys={{}} />)
    expect(container.innerHTML).toBe('')
    rerender(<SpellingKey keys={undefined} />)
    expect(container.innerHTML).toBe('')
    spelling = false
    rerender(<SpellingKey keys={{ 3: 'ع' }} />)
    expect(container.innerHTML).toBe('')
  })
})
