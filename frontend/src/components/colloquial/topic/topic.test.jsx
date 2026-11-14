// @vitest-environment happy-dom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import Dialogue from './Dialogue'
import Pairs from './Pairs'

afterEach(cleanup)

const lines = [
  { speaker: 'A', arabic: 'أهلا', transliteration: 'ahlan', english: 'Hello' },
  { speaker: 'B', arabic: 'أهلين', transliteration: 'ahleen', english: 'Hi there' },
]

describe('Dialogue', () => {
  it('ends on a Replay that keeps focus, not a disabled button that drops it', () => {
    render(<Dialogue lines={lines} />)
    const go = screen.getByRole('button', { name: 'Start the scene' })
    go.focus()
    fireEvent.click(go)
    fireEvent.click(screen.getByRole('button', { name: 'Next line' }))
    const end = screen.getByRole('button', { name: 'Replay' })
    expect(end.disabled).toBe(false)
    expect(document.activeElement).toBe(end)
    expect(screen.queryByRole('button', { name: 'Show all' })).toBeNull()
    fireEvent.click(end)
    expect(screen.getByRole('button', { name: 'Start the scene' })).toBeTruthy()
  })
})

describe('Pairs', () => {
  const pair = { pair: { arabic: 'إزيك؟', transliteration: 'ezzayyak', english: 'How are you?' }, response: { arabic: 'كويس', transliteration: 'kwayyis', english: 'Fine' } }
  it('a card is named by what it shows, so the answer is read once it is turned', () => {
    render(<Pairs pairs={[pair]} />)
    // The face showing says it turns, for the eye and the ear alike; the hidden face says nothing.
    const card = screen.getByRole('button', { name: /How are you\?.*Tap to see the answer/ })
    expect(screen.queryByRole('button', { name: /Fine/ })).toBeNull()
    fireEvent.click(card)
    expect(screen.getByRole('button', { name: /Fine.*Tap to turn it back/ })).toBe(card)
    expect(screen.queryByRole('button', { name: /see the answer/ })).toBeNull()
    expect(card.hasAttribute('aria-label')).toBe(false)
  })
})
