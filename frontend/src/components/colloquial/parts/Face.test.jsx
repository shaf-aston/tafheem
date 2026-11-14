// @vitest-environment happy-dom
// A phrase tile says how the phrase sounds in English letters, unless the learner turned that off.
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import Face from './Face'

afterEach(cleanup)
const phrase = { arabic: 'إِزَيّك؟', transliteration: 'ezzayyak?', english: 'How are you? (to a man)' }

describe('Face', () => {
  it('spells a tile out by default', () => {
    render(<Face phrase={phrase} index={0} spelt />)
    expect(screen.getByText('ezzayyak?')).toBeTruthy()
  })

  it('leaves the spelling to a caller that shows its own', () => {
    render(<Face phrase={phrase} index={0} />)
    expect(screen.queryByText('ezzayyak?')).toBeNull()
  })
  it('a tile with no picture holds its words in its middle, in the flow, so a short tile grows rather than cuts them', () => {
    render(<Face phrase={phrase} index={0} spelt />)
    const words = screen.getByText('ezzayyak?').parentElement
    expect(words.className).not.toMatch(/\babsolute\b/)
    expect(words.className).toMatch(/justify-center/)
  })

  it('a photo tile keeps its words at its foot, over the fade; its number is lifted over that fade and said by no one', () => {
    const { container } = render(<Face phrase={{ ...phrase, image: 'unit-01/x.jpg' }} index={4} spelt />)
    expect(screen.getByText('ezzayyak?').parentElement.className).toMatch(/\bbottom-0\b/)
    const number = container.querySelector('.tabular-nums')
    expect(number.textContent).toBe('05')
    expect(number.getAttribute('aria-hidden')).toBe('true')
    expect(number.className).toMatch(/layer-raised/)
    expect(container.firstChild.className).toMatch(/\bisolate\b/)   // lifted no further than its own tile
    expect(container.querySelector('img').getAttribute('alt')).toBe('')   // the English is printed: said once
  })
})
