// @vitest-environment happy-dom
// One pill for recent searches, root choices, filters and source references.
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import Chip from './Chip'

afterEach(cleanup)

describe('Chip', () => {
  it('is a button that answers a tap', () => {
    const onClick = vi.fn()
    render(<Chip onClick={onClick}>kataba</Chip>)
    fireEvent.click(screen.getByRole('button', { name: 'kataba' }))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('announces on/off only in a row where one is chosen', () => {
    render(<><Chip selected>on</Chip><Chip selected={false}>off</Chip><Chip>plain</Chip></>)
    expect(screen.getByRole('button', { name: 'on' }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByRole('button', { name: 'off' }).getAttribute('aria-pressed')).toBe('false')
    expect(screen.getByRole('button', { name: 'plain' }).hasAttribute('aria-pressed')).toBe(false)
  })

  it('with href is a link out, opened in a new tab', () => {
    render(<Chip href="https://sunnah.com/bukhari:1">Bukhari 1</Chip>)
    const link = screen.getByRole('link', { name: 'Bukhari 1' })
    expect(link.getAttribute('target')).toBe('_blank')
    expect(link.getAttribute('rel')).toContain('noopener')
  })

  it('puts Arabic on the small inline rung, so a mixed row stays one height', () => {
    render(<Chip arabic>كتب</Chip>)
    const word = screen.getByText('كتب')
    expect(word.className).toContain('arabic-tiny')
    expect(word.className).toContain('arabic-inline')
  })

  it('a cite with nothing to open is plain text, not a dead button', () => {
    render(<Chip cite accent="#0a7">Printed book</Chip>)
    expect(screen.queryByRole('button')).toBeNull()
    expect(screen.getByText('Printed book').tagName).toBe('SPAN')
  })
})
