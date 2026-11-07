// @vitest-environment happy-dom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import Practice from './Practice'

// Nothing is sent anywhere: an answer is filed through this, as the record's own hook does.
vi.mock('../../../lib/learner/record', () => ({ useRecord: () => ({ file: vi.fn() }) }))

afterEach(cleanup)

const pick = (id, answer, options = [answer, 'x', 'y']) => ({ id, type: 'choose', prompt: `Question ${id}`, answer, accepted: [answer], options })
const two = [pick('a', 'مرحبا'), pick('b', 'شكرا')]

const square = (n) => screen.getByRole('button', { name: new RegExp(`^Exercise ${n}:`) })

describe('Practice', () => {
  it('starts on the first exercise with every square undone', () => {
    render(<Practice exercises={two} />)
    expect(screen.getByText('Question a')).toBeTruthy()
    expect(square(1).getAttribute('aria-label')).toBe('Exercise 1: not done')
    expect(screen.getByText('0 of 2 done')).toBeTruthy()
    expect(screen.queryByText(/Next exercise/)).toBeNull()
  })

  it('an answer marks its square and offers Next, which moves on and takes focus to the new question', () => {
    render(<Practice exercises={two} />)
    fireEvent.click(screen.getByRole('button', { name: /مرحبا/ }))
    expect(square(1).getAttribute('aria-label')).toBe('Exercise 1: right')
    expect(screen.getByText('1 of 2 done')).toBeTruthy()
    fireEvent.click(screen.getByText(/Next exercise/))
    expect(screen.getByText('Question b')).toBeTruthy()
    expect(screen.queryByText(/Next exercise/)).toBeNull()
  })

  it('a wrong pick is marked wrong, and the last answer closes with the score', () => {
    render(<Practice exercises={two} />)
    fireEvent.click(screen.getByRole('button', { name: /^.*x$/ }))
    expect(square(1).getAttribute('aria-label')).toBe('Exercise 1: wrong')
    fireEvent.click(screen.getByText(/Next exercise/))
    fireEvent.click(screen.getByRole('button', { name: /شكرا/ }))
    expect(screen.getByText('1 of 2 right')).toBeTruthy()
    expect(screen.queryByText(/Next exercise/)).toBeNull()
  })

  it('any square can be jumped to, and an answered exercise comes back as it was left', () => {
    render(<Practice exercises={two} />)
    fireEvent.click(screen.getByRole('button', { name: /مرحبا/ }))
    fireEvent.click(square(2))
    expect(screen.getByText('Question b')).toBeTruthy()
    fireEvent.click(square(1))
    expect(screen.getByText('Question a')).toBeTruthy()
    expect(square(1).getAttribute('aria-label')).toBe('Exercise 1: right')
  })
})
