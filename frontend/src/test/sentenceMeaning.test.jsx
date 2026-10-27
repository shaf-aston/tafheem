// @vitest-environment happy-dom
// An English sentence shows its Arabic rendering, and each word as english → arabic.
import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import SentenceMeaning from '../components/ui/text/SentenceMeaning'

const source = { label: 'AI', confidence: 'guessed', detail: '' }
const data = {
  query: 'the book', kind: 'sentence', direction: 'en', meaning: 'الكتاب', source, ref: null,
  words: [{ arabic: '', english: 'the', base: 'the' }, { arabic: 'كتاب', english: 'book', base: 'book' }],
  words_source: source, left_out: [],
}

describe('SentenceMeaning', () => {
  it('shows the Arabic rendering and looks up the Arabic of a chip', () => {
    const onLookup = vi.fn()
    renderScreen(<SentenceMeaning data={data} accent="#0a7" onLookup={onLookup} />)
    expect(screen.getByText('الكتاب')).toBeTruthy()
    fireEvent.click(screen.getByText('book →').closest('button'))
    expect(onLookup).toHaveBeenCalledWith('كتاب')
    expect(screen.getByText('the →').closest('button').disabled).toBe(true)
  })
})
