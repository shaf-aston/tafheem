// @vitest-environment happy-dom
// The reader on a fake backend: a surah opens with its ayahs in its
// translation, the next surah replaces it, and another book replaces the English.
import { useState } from 'react'
import { describe, expect, it } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import QuranReader from '../components/quran/QuranReader'

const surah = (n, name, ayahs) => ({
  name_ar: name,
  ayah_count: ayahs.length,
  ayahs: ayahs.map((arabic, i) => ({ ayah: i + 1, arabic, english: `word gloss ${n}:${i + 1}` })),
})
const book = (prefix, n, count) => ({ ayahs: Object.fromEntries(Array.from({ length: count }, (_, i) => [i + 1, `${prefix} ${n}:${i + 1}`])) })

const ROUTES = {
  'GET /quran/surah/1': surah(1, 'الفاتحة', ['بِسْمِ ٱللَّهِ', 'ٱلْحَمْدُ لِلَّهِ']),
  'GET /quran/surah/2': surah(2, 'البقرة', ['الٓمٓ', 'ذَٰلِكَ ٱلْكِتَٰبُ', 'ٱلَّذِينَ يُؤْمِنُونَ']),
  'GET /quran/editions': [{ id: 'saheeh-en', short: 'Saheeh' }, { id: 'other-en', short: 'Other' }],
  'GET /quran/editions/surah/1': (config) => book(config.params.id, 1, 2),
  'GET /quran/editions/surah/2': (config) => book(config.params.id, 2, 3),
}

// The reader's place is its caller's, so the test holds it the way QuranLookup does.
function Reader() {
  const [place, setPlace] = useState({ surah: 1, ayah: null })
  return <QuranReader place={place} accent="#0a7" onGo={() => {}} onPlace={setPlace} onClose={() => {}} />
}

// The ayah rows, not the rail's numbers: a row is a toggle (aria-pressed).
const rows = () => screen.getAllByRole('button', { pressed: false }).filter((el) => el.closest('ol'))

describe('quran reader', () => {
  it('opens a surah with its ayahs, then steps to the next', async () => {
    renderScreen(<Reader />, { routes: ROUTES })
    expect(await screen.findByRole('button', { name: /saheeh-en 1:2/ })).toBeTruthy()
    expect(rows()).toHaveLength(2)

    fireEvent.click(screen.getByRole('button', { name: 'Next surah' }))
    expect(await screen.findByRole('button', { name: /saheeh-en 2:3/ })).toBeTruthy()
    expect(rows()).toHaveLength(3)
    expect(screen.queryByRole('button', { name: /1:1/ })).toBeNull()
  })

  it('puts another translation under every ayah', async () => {
    renderScreen(<Reader />, { routes: ROUTES })
    expect(await screen.findByRole('button', { name: /saheeh-en 1:1/ })).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Other' }))
    expect(await screen.findByRole('button', { name: /other-en 1:1/ })).toBeTruthy()
    expect(screen.queryByRole('button', { name: /saheeh-en/ })).toBeNull()
  })
})
