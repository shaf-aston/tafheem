// @vitest-environment happy-dom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import WordPairs from './WordPairs'

const words = [
  { id: 'fast', arabic: 'سريع', english: 'fast', transliteration: 'saree3', category: 'describing' },
  { id: 'slow', arabic: 'بطيء', english: 'slow', transliteration: 'batee2', category: 'opposites' },
  { id: 'hot', arabic: 'حار', english: 'hot', transliteration: '7aar', category: 'weather' },
  { id: 'cold', arabic: 'بارد', english: 'cold', transliteration: 'baarid', category: 'weather' },
]

afterEach(cleanup)

describe('WordPairs', () => {
  it('sets each word beside its other, in the order given, whatever their groups', () => {
    render(<WordPairs words={words} pairs={[['fast', 'slow'], ['hot', 'cold']]} />)
    expect(screen.getByText('2 pairs of opposites')).toBeTruthy()
    const rows = screen.getAllByRole('listitem').map((li) => li.textContent)
    expect(rows[0]).toContain('fast')
    expect(rows[0]).toContain('slow')
    expect(rows[1]).toContain('hot')
  })

  it('a pair missing a word is left out rather than shown half', () => {
    render(<WordPairs words={words} pairs={[['fast', 'slow'], ['hot', 'gone']]} />)
    expect(screen.getAllByRole('listitem')).toHaveLength(1)
  })

  it('hiding one side covers each opposite until it is tapped', () => {
    render(<WordPairs words={words} pairs={[['fast', 'slow'], ['hot', 'cold']]} />)
    fireEvent.click(screen.getByRole('button', { name: 'Hide one side' }))
    expect(screen.queryByText('slow')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Show the opposite of fast' }))
    expect(screen.getByText('slow')).toBeTruthy()
    expect(screen.queryByText('cold')).toBeNull()
  })
})
