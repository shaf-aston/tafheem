// @vitest-environment happy-dom
// The rest of an Ibn Faris entry: its English is one press away even when the
// rest is too short to be cut, and the Arabic opened whole stays whole.
import { describe, expect, it } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import RootMeaningCard from '../components/dictionary/RootMeaningCard'

const source = { key: 'maqayees', label: 'Maqayees al-Lugha (Ibn Faris)', confidence: 'verified', detail: '' }
const routes = {
  'GET /health': { root_meaning_status: 'ready' },
  'GET /dictionary/root-meaning': {
    root: 'نصر', status: 'ready', book_root: null, source,
    meaning: { core_meaning: 'إتيان خير', sarf_pattern: '', variances: [], rest: 'نصره ينصره نصرا', english: '' },
  },
  'GET /dictionary/root-meaning/english': { english: 'He helped him.', source },
  'GET /dictionary/root-meaning/english/lines': { lines: [{ arabic: 'نصره ينصره نصرا', english: 'He helped him.' }], source },
  'GET /dictionary/root-meaning/english/senses': {
    senses: [{ arabic: ['نصره ينصره نصرا'], word: 'نصره', say: 'naṣarahu', gloss: 'he helped him', examples: [] }], source,
  },
}

describe('RootMeaningCard', () => {
  it('offers the English of a rest too short to need a cut', async () => {
    const { asked } = renderScreen(<RootMeaningCard root="نصر" accent="#0a7" />, { routes })
    fireEvent.click(await screen.findByText('Read in English'))
    // Word by word first: the word, its Latin spelling and its meaning, beside the book's line.
    expect(await screen.findByText('— he helped him')).toBeTruthy()
    expect(screen.getByText('naṣarahu')).toBeTruthy()
    // Together was asked for on the same press, so switching to it waits on nothing;
    // One at a time's lines wait for that view, a model call nobody pressed for.
    expect(asked).toContain('GET /dictionary/root-meaning/english')
    expect(asked).not.toContain('GET /dictionary/root-meaning/english/lines')
    expect(screen.queryByText('Read in English')).toBeNull()
  })

  it('switches the words to Latin letters and hides the book\'s lines', async () => {
    renderScreen(<RootMeaningCard root="نصر" accent="#0a7" />, { routes })
    fireEvent.click(await screen.findByText('Read in English'))
    await screen.findByText('naṣarahu')
    expect(screen.getByText('نصره ينصره نصرا')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Latin' }))
    expect(screen.queryByText('نصره')).toBeNull()
    expect(screen.getByText('naṣarahu')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Hidden' }))
    expect(screen.queryByText('نصره ينصره نصرا')).toBeNull()
  })
})
