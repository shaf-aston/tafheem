// @vitest-environment happy-dom
// Sarf's core loop: a word typed and asked for comes back as its root and its
// gardaan. The meaning is left unlisted, so it fails the way a slow AI might,
// and the table still stands.
import { describe, expect, it } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import SarfPanel from '../components/SarfPanel'

const KATABA = {
  word: 'كتب',
  root: 'ك ت ب',
  wazn: 'فَعَلَ',
  verb_class: 'sahih',
  form: 'I-a-u',
  form_options: { 'I-a-u': 'I (فَعَلَ يَفْعُلُ)' },
  table: {
    columns: [{ id: 'madi', label: 'Past', arabic: 'ماضي' }],
    rows: [{ person: 'He', cells: { madi: 'كَتَبَ' } }],
  },
}

describe('sarf', () => {
  it('shows a word’s root and table', async () => {
    const { asked } = renderScreen(<SarfPanel accent="#0a7" onGo={() => {}} onVisit={() => {}} />, {
      routes: { 'POST /morphology': KATABA },
    })
    fireEvent.change(screen.getByLabelText(/^Arabic word/), { target: { value: 'كتب' } })
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))

    expect(await screen.findByRole('cell', { name: 'كَتَبَ' })).toBeTruthy()
    expect(screen.getByText('ك ت ب')).toBeTruthy()
    expect(screen.getByRole('rowheader', { name: 'He' })).toBeTruthy()
    expect(asked).toContain('POST /morphology')
  })
})
