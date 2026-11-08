// @vitest-environment happy-dom
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import settings from '../../../config/colloquial-display.json'
import WordMatch from './WordMatch'

afterEach(cleanup)

const make = (n) => Array.from({ length: n }, (_, i) => ({ id: `w${i}`, english: `word${i}`, arabic: `ك${'ب'.repeat(i + 1)}` }))
const en = (w) => within(screen.getByRole('list', { name: 'English' })).getByRole('button', { name: w.english })
const ar = (w) => within(screen.getByRole('list', { name: 'Arabic' })).getByRole('button', { name: w.arabic })
const status = () => screen.getByText(/matched/).textContent

describe('WordMatch', () => {
  it('a pair tapped together is found and its tiles go', () => {
    const words = make(3)
    render(<WordMatch words={words} />)
    expect(status()).toContain('0 of 3 matched')
    fireEvent.click(en(words[0]))
    fireEvent.click(ar(words[0]))
    expect(status()).toContain('1 of 3 matched')
    expect(en(words[0]).disabled).toBe(true)
    expect(ar(words[0]).disabled).toBe(true)
  })

  it('a wrong pair is a slip, marked with a sign as well as colour, and cleared by the next tap', () => {
    const words = make(3)
    render(<WordMatch words={words} />)
    fireEvent.click(en(words[0]))
    fireEvent.click(ar(words[1]))
    expect(status()).toContain('Not a pair.')
    expect(status()).toContain('1 slip')
    expect(en(words[0]).textContent).toContain('✕')
    fireEvent.click(en(words[2]))
    expect(status()).not.toContain('Not a pair.')
    expect(en(words[0]).textContent).not.toContain('✕')
  })

  it('two taps on one side only change the pick', () => {
    const words = make(3)
    render(<WordMatch words={words} />)
    fireEvent.click(en(words[0]))
    fireEvent.click(en(words[1]))
    expect(en(words[1]).getAttribute('aria-pressed')).toBe('true')
    expect(en(words[0]).getAttribute('aria-pressed')).toBe('false')
    expect(status()).toContain('0 slips')
  })

  it('finishing a board says so and offers to play again', () => {
    const words = make(2)
    render(<WordMatch words={words} />)
    for (const w of words) { fireEvent.click(en(w)); fireEvent.click(ar(w)) }
    expect(status()).toContain('All matched')
    fireEvent.click(screen.getByText('Play again'))
    expect(status()).toContain('0 of 2 matched')
  })

  it('a long topic is several even boards, never one with a tiny last', () => {
    const board = settings['match-board']
    render(<WordMatch words={make(board + 1)} />)
    expect(status()).toContain('board 1 of 2')
    expect(screen.getByRole('list', { name: 'English' }).children.length).toBe(Math.ceil((board + 1) / 2))
  })
})
