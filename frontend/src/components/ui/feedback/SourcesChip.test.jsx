// @vitest-environment happy-dom
// Several sources on one answer fold into one chip; one stays a badge.
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import SourcesChip from './SourcesChip'

afterEach(cleanup)

const rule = { key: 'rules', label: 'Sarf rule tables', confidence: 'derived', detail: 'A fixed table of patterns.' }
const lane = { key: 'lane', label: "Lane's Lexicon", confidence: 'verified' }
const machine = { key: 'ai', label: 'AI explanation', confidence: 'guessed' }

describe('SourcesChip', () => {
  it('draws nothing for no source, and a plain badge for one', () => {
    const { container, rerender } = render(<SourcesChip sources={[null, undefined]} />)
    expect(container.textContent).toBe('')
    rerender(<SourcesChip sources={[rule]} />)
    expect(screen.queryByRole('button')).toBeNull()
    expect(screen.getByText('Sarf rule tables')).toBeTruthy()
  })

  it('counts each source once, then lists them with their level on opening', () => {
    render(<SourcesChip sources={[rule, lane, { ...rule }]} />)
    const chip = screen.getByRole('button', { name: /Sources \(2\)/ })
    expect(screen.queryByText("Lane's Lexicon")).toBeNull()
    fireEvent.click(chip)
    expect(screen.getByText("Lane's Lexicon")).toBeTruthy()
    expect(screen.getByText('Checked by a person')).toBeTruthy()
    expect(screen.getByText('Worked out by a fixed rule')).toBeTruthy()
    expect(screen.getByText('A fixed table of patterns.')).toBeTruthy()
  })

  it('wears the weakest level on the chip, hidden text for a screen reader', () => {
    render(<SourcesChip sources={[lane, machine]} />)
    expect(screen.getByRole('button', { name: /A guess, can be wrong/ })).toBeTruthy()
  })

  it('closes on Escape and hands focus back to the chip', () => {
    render(<SourcesChip sources={[rule, lane]} />)
    const chip = screen.getByRole('button', { name: /Sources/ })
    fireEvent.click(chip)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByText("Lane's Lexicon")).toBeNull()
    expect(document.activeElement).toBe(chip)
  })
})
