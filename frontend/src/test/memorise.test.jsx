// @vitest-environment happy-dom
// Filling a page in: a gap answered right is counted right, one answered wrong
// is counted wrong and shows the word it should have been.
import { describe, expect, it } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import MemorisePanel from '../components/MemorisePanel'

// Every word on the page is the same word, so whichever ones are taken out,
// the right answer to each is known.
const WORD = 'كلمة'
const AYAH = (n) => ({ ayah: n, arabic: Array(6).fill(WORD).join(' '), english: '', page: 1 })
const routes = {
  'GET /quran/surah/1': { surah: 1, name_en: 'Al-Fatihah', name_ar: 'الفاتحة', ayahs: [1, 2, 3].map(AYAH) },
}

describe('Memorise', () => {
  it('marks a page: right gaps counted, missed ones shown', async () => {
    renderScreen(<MemorisePanel accent="#0a7" onGo={() => {}} onVisit={() => {}} />, { routes })
    const gaps = await screen.findAllByLabelText(/missing word/)
    expect(gaps.length).toBeGreaterThan(1)
    fireEvent.change(gaps[0], { target: { value: WORD } })
    fireEvent.change(gaps[1], { target: { value: 'خطأ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Check this page' }))

    expect(await screen.findByText(new RegExp(`^1 of ${gaps.length} right`))).toBeTruthy()
    // The missed word is printed under every gap not answered right.
    expect(screen.getAllByText(WORD, { selector: '.text-\\[var\\(--danger\\)\\]' })).toHaveLength(gaps.length - 1)
    expect(gaps.every((gap) => gap.readOnly)).toBe(true)

    fireEvent.click(screen.getByRole('button', { name: 'Try this page again' }))
    expect(screen.getAllByLabelText(/missing word/).map((gap) => gap.value)).toEqual(gaps.map(() => ''))
  })
})
