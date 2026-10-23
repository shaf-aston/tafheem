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
}

describe('RootMeaningCard', () => {
  it('offers the English of a rest too short to need a cut', async () => {
    const { asked } = renderScreen(<RootMeaningCard root="نصر" accent="#0a7" />, { routes })
    fireEvent.click(await screen.findByText('Read in English'))
    expect(await screen.findByText('He helped him.')).toBeTruthy()
    // Both shapes were asked for on the one press, so switching view waits on nothing.
    expect(asked).toContain('GET /dictionary/root-meaning/english/lines')
    expect(screen.queryByText('Read in English')).toBeNull()
  })
})
