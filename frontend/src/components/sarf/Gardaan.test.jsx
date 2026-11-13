// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'

import Gardaan from './Gardaan'

afterEach(cleanup)

const table = {
  columns: [{ id: 'past', label: 'Past', arabic: 'ماضي' }, { id: 'present', label: 'Present', arabic: 'مضارع' }],
  rows: [{ person: 'he', cells: { past: 'كَتَبَ', present: 'يَكْتُبُ' } }],
}

describe('Gardaan', () => {
  it('lets a keyboard reach the table that scrolls sideways on a phone', () => {
    render(<Gardaan table={table} accent="var(--c)" form="" options={{}} onForm={vi.fn()} />)
    const box = screen.getByRole('region', { name: /conjugation table/i })
    expect(box.getAttribute('tabindex')).toBe('0')
    expect(box.querySelector('table')).not.toBeNull()
  })
})
