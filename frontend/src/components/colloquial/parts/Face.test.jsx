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
})
