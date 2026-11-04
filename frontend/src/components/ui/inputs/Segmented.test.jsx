// @vitest-environment happy-dom
// The one-of-several switch (views, scripts, dialects) on twenty-four screens.
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import Segmented from './Segmented'

afterEach(cleanup)

const options = [{ id: 'tree', label: 'Tree' }, { id: 'list', label: 'List' }]

describe('Segmented', () => {
  it('is a named group with exactly the chosen option pressed', () => {
    render(<Segmented label="View" options={options} value="list" onChange={() => {}} />)
    expect(screen.getByRole('group', { name: 'View' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Tree' }).getAttribute('aria-pressed')).toBe('false')
    expect(screen.getByRole('button', { name: 'List' }).getAttribute('aria-pressed')).toBe('true')
  })

  it('hands back the id of the option tapped', () => {
    const onChange = vi.fn()
    render(<Segmented label="View" options={options} value="list" onChange={onChange} />)
    fireEvent.click(screen.getByRole('button', { name: 'Tree' }))
    expect(onChange).toHaveBeenCalledWith('tree')
  })

  it('captioned shows its label as an eyebrow beside the row', () => {
    render(<Segmented label="View" captioned options={options} value="tree" onChange={() => {}} />)
    expect(screen.getByText('View').className).toContain('eyebrow')
  })
})
