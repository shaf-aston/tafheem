// @vitest-environment happy-dom
// One quiet row over the page: the part, the page and one Settings pill, and
// every choice that used to stand above the page is still in its sheet.
import { describe, expect, it } from 'vitest'
import { fireEvent, screen, within } from '@testing-library/react'

import { renderScreen } from '../../test/render'
import MemorisePanel from './MemorisePanel'

const AYAH = (n) => ({ ayah: n, arabic: Array(6).fill('كلمة').join(' '), english: 'A word', page: 1 })
const routes = { 'GET /quran/surah/1': { surah: 1, name_en: 'Al-Fatihah', name_ar: 'الفاتحة', ayahs: [1, 2, 3].map(AYAH) } }

describe('Memorise settings row', () => {
  it('puts the choices behind one Settings pill, all still reachable', async () => {
    renderScreen(<MemorisePanel accent="#0a7" onGo={() => {}} onVisit={() => {}} />, { routes })
    await screen.findAllByLabelText(/missing word/)
    // Nothing chosen once and left stands over the page any more.
    expect(screen.queryByRole('group', { name: 'How you answer' })).toBeNull()
    expect(screen.queryByRole('button', { name: /translation/i })).toBeNull()

    // The pill says what is chosen in words, not "1 in 3".
    expect(screen.getByRole('button', { name: /^Settings/ }).textContent).toMatch(/1 word in 3 hidden/)

    fireEvent.click(screen.getByRole('button', { name: /^Settings/ }))
    const sheet = await screen.findByRole('dialog')
    for (const caption of ['How you answer', 'Book', 'How much is missing', 'Translation']) {
      expect(within(sheet).getByText(caption)).toBeTruthy()
    }
    // New gaps moved under the page, beside the page turns.
    expect(screen.getByRole('button', { name: 'New gaps' })).toBeTruthy()
  })
})
