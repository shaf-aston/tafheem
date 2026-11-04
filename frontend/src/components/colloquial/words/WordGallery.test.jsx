// @vitest-environment happy-dom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import WordGallery from './WordGallery'

const words = [
  { id: 'red', arabic: 'أحمر', english: 'red', transliteration: 'a7mar', category: 'colours' },
  { id: 'blue', arabic: 'أزرق', english: 'blue', transliteration: 'azra2', category: 'colours' },
  { id: 'green', arabic: 'أخضر', english: 'green', transliteration: 'akhdar', category: 'colours' },
  { id: 'wood', arabic: 'خشب', english: 'wood', transliteration: 'khashab', category: 'materials' },
  { id: 'iron', arabic: 'حديد', english: 'iron', transliteration: '7adeed', category: 'materials' },
  { id: 'glass', arabic: 'زجاج', english: 'glass', transliteration: 'zujaaj', category: 'materials' },
]

const renderWithProviders = (node) => render(<QueryClientProvider client={new QueryClient()}>{node}</QueryClientProvider>)

afterEach(cleanup)

describe('WordGallery', () => {
  it('shows every word as a tile under its heading, numbered on across headings', () => {
    renderWithProviders(<WordGallery words={words} />)
    expect(screen.getByRole('heading', { name: 'colours' })).toBeTruthy()
    expect(screen.getByRole('heading', { name: 'materials' })).toBeTruthy()
    expect(screen.getAllByRole('button')).toHaveLength(6)
    expect(screen.getByText('04')).toBeTruthy()
  })

  it('opens a tile in the sheet and steps on into the next heading', () => {
    renderWithProviders(<WordGallery words={words} />)
    fireEvent.click(screen.getByRole('button', { name: 'green (أخضر)' }))
    expect(screen.getByText('3 / 6')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Next word' }))
    expect(screen.getByText('4 / 6')).toBeTruthy()
    expect(screen.queryByText('Other dialects')).toBeNull()
  })
  it('puts a heading\'s pictured words first and draws only a pictured tile large', () => {
    const pictured = ['cat', 'dog', 'cow', 'hen', 'goat', 'duck', 'fish']
      .map((en, n) => ({ id: en, arabic: `ص${n}`, english: en, category: 'little', image: `emoji/${en}.svg` }))
    const mixed = [{ id: 'i', arabic: 'أنا', english: 'I', category: 'little' }, ...pictured]
    const { container } = renderWithProviders(<WordGallery words={mixed} />)
    const names = screen.getAllByRole('button').map((b) => b.getAttribute('aria-label'))
    expect(names[0]).toBe('cat (ص0)')
    expect(names.at(-1)).toBe('I (أنا)')
    const big = container.querySelectorAll('li.col-span-2')
    expect(big).toHaveLength(1)
    expect(big[0].textContent).toContain('cat')
  })

  it('draws no large tile when a run is too short to fill the rows beside it', () => {
    const few = [{ id: 'cat', arabic: 'قطة', english: 'cat', category: 'x', image: 'emoji/cat.svg' }]
    const { container } = renderWithProviders(<WordGallery words={few} />)
    expect(container.querySelectorAll('li.col-span-2')).toHaveLength(0)
  })
})
