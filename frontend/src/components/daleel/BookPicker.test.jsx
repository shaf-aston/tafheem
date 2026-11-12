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
  it('is one line until asked for, and opens in one press', () => {
    render(<BookPicker {...props} />)
    expect(screen.queryByLabelText('Search the list of books')).toBeNull()
    expect(screen.getByText('Searching all 2 books')).toBeTruthy()
    fireEvent.click(screen.getByText('Choose books'))
    expect(screen.getByLabelText('Search the list of books')).toBeTruthy()
    expect(screen.getByText('Hide books').getAttribute('aria-expanded')).toBe('true')
  })

  it('folds again when a new set of answers arrives', () => {
    const { rerender } = render(<BookPicker {...props} answered />)
    fireEvent.click(screen.getByText('Choose books'))
    rerender(<BookPicker {...props} answered={false} />)
    rerender(<BookPicker {...props} answered />)
    expect(screen.queryByLabelText('Search the list of books')).toBeNull()
  })
})
