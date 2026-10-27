// @vitest-environment happy-dom
// The Terms view on a fixture guide: groups on a phone, one group's chart on a tap, a term's card on another; the
// whole tree from the wide breakpoint, drawn no smaller than keeps a term's label at 12px; the card's hadith list
// saying so (not an error) where the rulings index is not built.
import { useState } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'

import { renderScreen } from '../../test/render'
import { MIN_SCALE, SMALLEST_LABEL } from '../../lib/hadith/termsChart'
import TermsView from './TermsView'

const term = (arabic, en, more = {}) => ({ arabic, en, meaning: `${en} means this.`, lugha: '', quote: '', source: 'Taqrib', page: 'p. 4', kind: '', answers: {}, confuse: [], kids: [], ...more })
const guide = {
  scale: [], link_rules: null,
  glossary: [
    {
      title: 'Accepted', name: 'المقبول', by: 'How sure is the report?', axes: [{ id: 'memory', q: 'The narrator\'s memory' }],
      terms: [
        term('الصحيح', 'Sahih', { lugha: 'Sound, whole', kind: 'sahih', answers: { memory: 'Full' }, confuse: [{ arabic: 'الحسن', why: 'Both are accepted.' }], kids: [term('لذاته', 'In itself')] }),
        term('الحسن', 'Hasan', { answers: { memory: 'Light' } }),
      ],
    },
    { title: 'Rejected', name: 'المردود', by: 'What is wrong with it?', axes: [], terms: [term('الضعيف', 'Weak')] },
  ],
}
// The panel owns the open group (the place string); here a state does.
function Harness() {
  const [group, setGroup] = useState(null)
  return <TermsView accent="red" onOpen={() => {}} group={group} onGroup={setGroup} />
}
const routes = { 'GET /usul/guide': guide }

const media = (wide) => vi.stubGlobal('matchMedia', () => ({ matches: wide, addEventListener() {}, removeEventListener() {} }))
afterEach(() => vi.unstubAllGlobals())

describe('TermsView on a phone', () => {
  it('lists the groups with the question each splits on', async () => {
    media(false)
    renderScreen(<Harness />, { routes })
    expect(await screen.findByRole('button', { name: /Accepted/ })).toBeTruthy()
    expect(screen.getByText('How sure is the report?')).toBeTruthy()
    expect(screen.queryByRole('img', { name: /Hadith terms/ })).toBeNull()
  })

  it('draws a group on a tap, and a term\'s card on a tap of the term', async () => {
    media(false)
    renderScreen(<Harness />, { routes })
    fireEvent.click(await screen.findByRole('button', { name: /Accepted/ }))
    expect(screen.queryByRole('img')).toBeNull()
    expect(screen.getByText('In itself')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /Sahih الصحيح/ }))
    const card = await screen.findByRole('dialog')
    expect(within(card).getByText('Sahih means this.')).toBeTruthy()
    expect(within(card).getByText('In the language')).toBeTruthy()
    expect(within(card).getByText('Often confused with')).toBeTruthy()
    // Both answer the memory question, so the two lie side by side.
    expect(within(card).getByText('The narrator\'s memory')).toBeTruthy()
    expect(within(card).getByText('Full')).toBeTruthy()
    expect(within(card).getByText('Light')).toBeTruthy()
  })

  it('says no hadith carry the ruling where the rulings index is not built', async () => {
    media(false)
    renderScreen(<Harness />, { routes })
    fireEvent.click(await screen.findByRole('button', { name: /Accepted/ }))
    fireEvent.click(screen.getByRole('button', { name: /Sahih الصحيح/ }))
    expect(await screen.findByText('No hadith carry this ruling.')).toBeTruthy()
    expect(screen.queryByText(/could not/i)).toBeNull()
  })

  it('says so when the glossary is empty', async () => {
    media(false)
    renderScreen(<Harness />, { routes: { 'GET /usul/guide': { glossary: [] } } })
    expect(await screen.findByText('No terms are built yet.')).toBeTruthy()
  })
})

describe('TermsView from the wide breakpoint', () => {
  it('draws the whole tree no smaller than keeps a label at 12px', async () => {
    media(true)
    renderScreen(<Harness />, { routes })
    const chart = await screen.findByRole('group', { name: 'Hadith terms' })
    const width = Number(chart.getAttribute('viewBox').split(' ')[2])
    expect(width).toBeGreaterThan(0)
    // The zoom bar takes it a step in and back to fitted.
    fireEvent.click(screen.getByRole('button', { name: 'Zoom in' }))
    expect(screen.getByText('125%')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Fit' }))
    expect(screen.getByText('100%')).toBeTruthy()
    expect(SMALLEST_LABEL * MIN_SCALE).toBeGreaterThanOrEqual(12)
    expect(chart.getAttribute('role')).toBe('group')
    // A term of the whole tree opens its card.
    fireEvent.click(screen.getByText('الضعيف').closest('g[role=button]'))
    await waitFor(() => expect(screen.getByRole('dialog')).toBeTruthy())
  })
})
