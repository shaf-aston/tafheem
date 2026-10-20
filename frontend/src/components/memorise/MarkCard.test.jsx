// @vitest-environment happy-dom
import { useState } from 'react'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import Line from './Line'

const WORDS = ['إِيَّاكَ', 'نَعْبُدُ']
const MARKS = [
  { word: WORDS[0], state: 'said', heard: '', said: 'إِيَّاكَ' },
  // Wrong on sound with the letters right: the ear wrote the word with a vowel off.
  { word: WORDS[1], state: 'wrong', heard: '', said: 'نَعْبِدُ', sure: 0.41, weak: 'ع', weakFrom: 2, at: 2.4, take: 1 },
]

function Page({ marks = MARKS }) {
  const [open, setOpen] = useState(null)
  const recite = { words: marks, extras: [], at: 2, from: 0, shown: new Set(), open, setOpen, takeAudio: () => undefined }
  return (
    <Line
      line={{ id: 'a', label: '1:5', arabic: WORDS.join(' ') }}
      flow
      index={0}
      blanks={new Set()}
      answers={{}}
      accent="var(--primary)"
      recite={recite}
      onStartAt={() => {}}
    />
  )
}

afterEach(cleanup)

describe('the word card', () => {
  it('opens under a wrong word with what was heard, vowelled, and how sure the model was', () => {
    render(<Page />)
    fireEvent.click(screen.getByRole('button', { name: /نَعْبُدُ, wrong/ }))
    const card = screen.getByRole('dialog')
    expect(card.textContent).toContain('نَعْبِدُ')
    expect(card.textContent).toContain('Model sure it was said right: 41%')
    expect(card.textContent).toContain('The letters matched but the sound did not')
    // No recording was kept, so there is nothing of the reader's own to play.
    expect(screen.queryByText(/Mine/)).toBeNull()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('opens an ayah card from its number, listing the problem words', () => {
    render(<Page />)
    fireEvent.click(screen.getByRole('button', { name: 'ayah 5' }))
    expect(screen.getByRole('dialog').textContent).toContain('1 right, 1 wrong')
  })

  it('stays open, as waiting, when its word flips back, and leaves zero counts out', () => {
    const { rerender } = render(<Page />)
    fireEvent.click(screen.getByRole('button', { name: /نَعْبُدُ, wrong/ }))
    rerender(<Page marks={[MARKS[0], { word: WORDS[1], state: 'waiting', heard: '', said: '' }]} />)
    const card = screen.getByRole('dialog')
    expect(card.textContent).toContain('Not reached yet.')
    expect(card.textContent).toContain('waiting')
    fireEvent.keyDown(document, { key: 'Escape' })
    rerender(<Page marks={[MARKS[0], { ...MARKS[0], word: WORDS[1] }]} />)
    fireEvent.click(screen.getByRole('button', { name: 'ayah 5' }))
    expect(screen.getByRole('dialog').textContent).toContain('All right')
  })
})
