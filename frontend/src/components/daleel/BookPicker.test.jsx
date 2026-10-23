// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'

import BookPicker from './BookPicker'

afterEach(cleanup)

const books = [
  { name: 'Lane', source: 'lane', category: 'Dictionary', english: '' },
  { name: 'مختصر القدوري', source: 'openiti', category: 'Fiqh', english: 'Mukhtasar al-Quduri' },
]
const props = { books, onChange: vi.fn(), accent: 'var(--c)', sourceLabel: (key) => key }

describe('BookPicker', () => {
  it('shows the list while there is nothing else on the page', () => {
    render(<BookPicker {...props} />)
    expect(screen.getByLabelText('Search the list of books')).toBeTruthy()
    expect(screen.queryByText('Choose books')).toBeNull()
  })

  it('folds to its one line once answers are shown, and opens in one press', () => {
    render(<BookPicker {...props} folded />)
    expect(screen.queryByLabelText('Search the list of books')).toBeNull()
    expect(screen.getByText('Searching all 2 books')).toBeTruthy()
    fireEvent.click(screen.getByText('Choose books'))
    expect(screen.getByLabelText('Search the list of books')).toBeTruthy()
    expect(screen.getByText('Hide books').getAttribute('aria-expanded')).toBe('true')
  })

  it('folds again when a new set of answers arrives', () => {
    const { rerender } = render(<BookPicker {...props} folded />)
    fireEvent.click(screen.getByText('Choose books'))
    rerender(<BookPicker {...props} folded={false} />)
    rerender(<BookPicker {...props} folded />)
    expect(screen.queryByLabelText('Search the list of books')).toBeNull()
  })
})
