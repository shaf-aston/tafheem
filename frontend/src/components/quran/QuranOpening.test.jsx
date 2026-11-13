// @vitest-environment happy-dom
// The Qur'an tab with nothing open: today's ayah from the backend, where the
// reader stopped from the journey, and the search box still under them.
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from '../../test/render'
import { todayAyah } from '../../lib/quran/todayAyah'
import QuranPanel from './QuranPanel'

const journey = vi.hoisted(() => ({ steps: [], at: -1 }))
vi.mock('../../lib/nav/journey', async (actual) => ({ ...(await actual()), useJourney: () => journey }))

const { surah, ayah } = todayAyah()
const ROUTES = {
  [`GET /quran/${surah}/${ayah}`]: { surah, ayah, arabic_text: 'نص', words: [{ arabic: 'نص', uthmani: 'نَصّ' }, { arabic: 'آخر' }] },
  [`GET /quran/editions/${surah}/${ayah}`]: { surah, ayah, passages: [{ text: 'The English line.' }] },
}

const panel = () => <QuranPanel accent="#0a7" onGo={() => {}} onVisit={() => {}} />

describe('the Qur’an tab opening', () => {
  afterEach(() => Object.assign(journey, { steps: [], at: -1 }))

  it("shows today's ayah under the search box, and no Continue with nowhere stopped", async () => {
    renderScreen(panel(), { routes: ROUTES })
    const today = await screen.findByRole('button', { name: /The English line\./ })
    expect(today.textContent).toContain('نَصّ آخر')
    expect(today.textContent).toContain(`${surah}:${ayah}`)
    expect(screen.queryByRole('region', { name: 'Where you stopped' })).toBeNull()
    // The box first: on a phone it was under today's ayah, below the fold.
    expect(today.compareDocumentPosition(screen.getByPlaceholderText(/2:255/)) & Node.DOCUMENT_POSITION_PRECEDING).toBeTruthy()
  })

  it('offers to carry on from the last ayah read', async () => {
    Object.assign(journey, { steps: [{ tab: 'quran', value: '2:255' }, { tab: 'dict', value: 'كتب' }], at: 1 })
    renderScreen(panel(), { routes: ROUTES })
    const stopped = await screen.findByRole('region', { name: 'Where you stopped' })
    expect(stopped.textContent).toContain('Al-Baqarah')
    expect(stopped.textContent).toContain('2:255')
  })

  it('opening the ayah puts the opening away for the reader', async () => {
    renderScreen(panel(), { routes: ROUTES })
    fireEvent.click(await screen.findByRole('button', { name: /The English line\./ }))
    expect(screen.queryByRole('region', { name: 'Today’s ayah' })).toBeNull()
  })

  it('leaves the card out when the backend does not answer', async () => {
    renderScreen(panel())
    expect(await screen.findByRole('heading', { name: /Quran/ })).toBeTruthy()
    await vi.waitFor(() => expect(screen.queryByRole('region', { name: 'Today’s ayah' })).toBeNull())
  })
})
