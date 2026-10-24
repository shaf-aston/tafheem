// @vitest-environment happy-dom
// The Map as a tab: every screen it shows is an address. Index → chart → a box inside it → back up; the methodologies
// from family to group to a comparison; and an address arriving (back, forward, a link) opens the screen it names.
import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'

import MapPanel from '../components/map/MapPanel'

afterEach(cleanup)

const click = (name) => fireEvent.click(screen.getByRole('button', { name }))

describe('the map', () => {
  it('writes every step into the address, and walks back up', () => {
    const visits = []
    render(<MapPanel incoming={null} onVisit={(value) => visits.push(value)} />)

    fireEvent.click(screen.getByRole('button', { name: /Arabic Language/ }))
    expect(visits.at(-1)).toBe('07')
    expect(screen.getByRole('region', { name: 'Arabic Language chart' })).toBeTruthy()

    // A box with more inside zooms, and the trail names the way back.
    const deeper = screen.getAllByRole('button').find((button) => button.closest('[role=region]') && button.textContent.includes('›'))
    fireEvent.click(deeper)
    expect(visits.at(-1)).toMatch(/^07\/\d+(\/\d+)?$/)
    const trail = screen.getByRole('navigation', { name: 'Map trail' })
    expect(trail.textContent).toMatch(/^Map›Arabic Language›/)

    click('Up one level')
    expect(visits.at(-1)).toBe('07')
    fireEvent.keyDown(screen.getByRole('heading', { name: 'Arabic Language' }), { key: 'Escape' })
    expect(visits.at(-1)).toBe(null)
    expect(screen.getByRole('button', { name: /Methodologies/ })).toBeTruthy()
  })

  it('gives the methodologies a family, a group and a comparison of their own', () => {
    const visits = []
    render(<MapPanel incoming={null} onVisit={(value) => visits.push(value)} />)

    click(/Beyond the sciences/)
    expect(visits.at(-1)).toBe('manhaj/creed')
    fireEvent.click(screen.getByRole('tab', { name: /Schools of law/ }))
    expect(visits.at(-1)).toBe('manhaj/fiqh')
    fireEvent.click(screen.getByRole('button', { name: /Ḥanafī/ }))
    expect(visits.at(-1)).toBe('manhaj/fiqh/hanafi')
    fireEvent.change(screen.getByRole('combobox', { name: /Compare with/ }), { target: { value: 'maliki' } })
    expect(visits.at(-1)).toBe('manhaj/fiqh/hanafi/maliki')
    expect(screen.getByText(/^Differ on/)).toBeTruthy()

    click('Methodologies')
    expect(visits.at(-1)).toBe('manhaj/fiqh')
  })

  it('opens the screen an arriving address names', () => {
    const { rerender } = render(<MapPanel incoming="manhaj/creed/ibadi" arrival={1} />)
    expect(screen.getByRole('heading', { name: 'Ibāḍī' })).toBeTruthy()
    expect(screen.getByText('Core beliefs')).toBeTruthy()

    // Back to the chart a reader had zoomed into: the trail is that deep again.
    rerender(<MapPanel incoming="07/0" arrival={2} />)
    expect(screen.getByRole('navigation', { name: 'Map trail' }).querySelectorAll('li')).toHaveLength(3)

    rerender(<MapPanel incoming={null} arrival={3} />)
    expect(screen.queryByRole('navigation', { name: 'Map trail' })).toBeNull()
    expect(screen.getAllByRole('button', { name: /Beyond the sciences/ })).toHaveLength(1)
  })
})
