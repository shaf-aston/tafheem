// @vitest-environment happy-dom
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import WheelPicker from './WheelPicker'

const options = [{ id: 'eg', label: 'Egyptian' }, { id: 'lev', label: 'Levantine' }]
afterEach(cleanup)

describe('WheelPicker: its button is named by what it shows', () => {
  it('says the choice first, then what it is a choice of: what a voice-control user sees is what they can say', () => {
    render(<WheelPicker label="Dialect" options={options} value="eg" onChange={() => {}} />)
    const pill = screen.getByRole('button', { name: 'Egyptian, Dialect' })
    expect(pill.textContent).toContain('Egyptian')
  })

  it('says the placeholder when nothing is chosen, and only the label when the two are the same', () => {
    render(<WheelPicker label="Surah" placeholder="Pick one" options={options} value={null} onChange={() => {}} />)
    expect(screen.getByRole('button', { name: 'Pick one, Surah' })).toBeTruthy()
    cleanup()
    render(<WheelPicker label="Surah" placeholder="Surah" options={options} value={null} onChange={() => {}} />)
    expect(screen.getByRole('button', { name: 'Surah' })).toBeTruthy()
  })
})
