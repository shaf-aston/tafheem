// @vitest-environment happy-dom
// Grow's one-answer options: numbered, picked by digit, set two by two when short.
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import OneOf from './OneOf'

const short = [{ id: 'a', text: 'the book' }, { id: 'b', text: 'a book' }, { id: 'c', text: 'books' }, { id: 'd', text: 'a books' }]
const long = [{ id: 'a', text: 'A Sunnah the Prophet kept up and rarely left' }, { id: 'b', text: 'b' }]
const three = short.slice(0, 3)

afterEach(cleanup)

describe('OneOf', () => {
  it('numbers each answer, the number left out of its name', () => {
    render(<OneOf options={short} answer="a" value={null} setValue={() => {}} result={null} label="Answers" />)
    expect(screen.getAllByRole('radio').map((radio) => radio.firstChild.textContent)).toEqual(['1', '2', '3', '4'])
    expect(screen.getByRole('radio', { name: 'a book' })).toBeTruthy()
  })

  it('picks with its digit, and keeps the digit from the tab shortcuts', () => {
    const setValue = vi.fn()
    const tabs = vi.fn()
    window.addEventListener('keydown', tabs)
    render(<OneOf options={short} answer="a" value={null} setValue={setValue} result={null} label="Answers" />)
    fireEvent.keyDown(window, { key: '2' })
    expect(setValue).toHaveBeenCalledWith('b')
    expect(tabs).not.toHaveBeenCalled()
    fireEvent.keyDown(window, { key: '5' })
    expect(setValue).toHaveBeenCalledTimes(1)
    expect(tabs).toHaveBeenCalledTimes(1)
    window.removeEventListener('keydown', tabs)
  })

  it('does not change the answer once checked', () => {
    const setValue = vi.fn()
    render(<OneOf options={short} answer="a" value="b" setValue={setValue} result="wrong" label="Answers" />)
    fireEvent.keyDown(window, { key: '1' })
    expect(setValue).not.toHaveBeenCalled()
    expect(screen.getByRole('radio', { name: 'the book' }).dataset.mark).toBe('right')
    expect(screen.getByRole('radio', { name: 'a book' }).dataset.mark).toBe('wrong')
  })

  it('sets short answers two by two when they pair evenly, long English a row each', () => {
    const { rerender } = render(<OneOf options={short} answer="a" value={null} setValue={() => {}} result={null} label="A" />)
    expect(screen.getByRole('radiogroup').classList.contains('grow-options-two')).toBe(true)
    rerender(<OneOf options={long} answer="a" value={null} setValue={() => {}} result={null} label="A" />)
    expect(screen.getByRole('radiogroup').classList.contains('grow-options-two')).toBe(false)
    rerender(<OneOf options={long} answer="a" value={null} setValue={() => {}} result={null} arabic label="A" />)
    expect(screen.getByRole('radiogroup').classList.contains('grow-options-two')).toBe(true)
    rerender(<OneOf options={three} answer="a" value={null} setValue={() => {}} result={null} arabic label="A" />)
    expect(screen.getByRole('radiogroup').classList.contains('grow-options-two')).toBe(false)
  })
})
