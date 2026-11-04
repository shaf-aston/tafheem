// @vitest-environment happy-dom
// The one box every tab types into: a change here lands on fourteen screens at once.
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import SearchBox from './SearchBox'

afterEach(cleanup)

const box = (props) => render(
  <SearchBox id="q" label="Word" value="" onChange={() => {}} {...props} />
)

describe('SearchBox', () => {
  it('writes its hint from the verb, adding the microphone when one sits beside it', () => {
    box({ verb: 'search', onSubmit: () => {} })
    expect(screen.getByText('Enter to search')).toBeTruthy()
    cleanup()
    box({ verb: 'search', onSubmit: () => {}, children: <button type="button">mic</button> })
    expect(screen.getByText('Enter to search, or say it')).toBeTruthy()
  })

  it('a filter (no onSubmit) has no return button, no hint, and Enter does nothing', () => {
    box({ verb: 'search', value: 'kataba' })
    expect(screen.queryByRole('button', { name: 'Search' })).toBeNull()
    expect(screen.queryByText(/Enter to/)).toBeNull()
    fireEvent.keyDown(screen.getByLabelText('Word'), { key: 'Enter' })
  })

  it('Enter submits; Shift+Enter in a multiline box is a new line, not a submit', () => {
    const onSubmit = vi.fn()
    box({ value: 'كتب', onSubmit, multiline: true })
    const field = screen.getByLabelText('Word')
    expect(field.tagName).toBe('TEXTAREA')
    fireEvent.keyDown(field, { key: 'Enter', shiftKey: true })
    expect(onSubmit).not.toHaveBeenCalled()
    fireEvent.keyDown(field, { key: 'Enter' })
    expect(onSubmit).toHaveBeenCalledTimes(1)
  })

  it('turns right to left on the first Arabic letter', () => {
    box({ value: 'kataba', onSubmit: () => {} })
    expect(screen.getByLabelText('Word').getAttribute('dir')).toBe('ltr')
    cleanup()
    box({ value: 'كتب', onSubmit: () => {} })
    const field = screen.getByLabelText('Word')
    expect(field.getAttribute('dir')).toBe('rtl')
    expect(field.getAttribute('lang')).toBe('ar')
  })

  it('the return button waits for text, and for a busy search to finish', () => {
    box({ value: '  ', onSubmit: () => {} })
    expect(screen.getByRole('button', { name: 'Search' }).disabled).toBe(true)
    cleanup()
    box({ value: 'كتب', onSubmit: () => {}, busy: true })
    expect(screen.getByRole('button', { name: 'Search' }).disabled).toBe(true)
    cleanup()
    const onSubmit = vi.fn()
    box({ value: 'كتب', onSubmit })
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))
    expect(onSubmit).toHaveBeenCalledTimes(1)
  })

  it('clear shows only with text, and empties the box unless the tab clears it itself', () => {
    box({ onSubmit: () => {} })
    expect(screen.queryByRole('button', { name: 'Clear search' })).toBeNull()
    cleanup()
    const onChange = vi.fn()
    box({ value: 'كتب', onChange, onSubmit: () => {} })
    fireEvent.click(screen.getByRole('button', { name: 'Clear search' }))
    expect(onChange).toHaveBeenCalledWith('')
    cleanup()
    const onClear = vi.fn()
    box({ value: 'كتب', onChange, onClear, onSubmit: () => {} })
    fireEvent.click(screen.getByRole('button', { name: 'Clear search' }))
    expect(onClear).toHaveBeenCalledTimes(1)
  })
})
