// @vitest-environment happy-dom
// The quiz's core loop on the real word banks: a question comes up, a pick
// gets a verdict on the option itself, and the options lock.
import { afterEach, describe, expect, it } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'

import { renderScreen } from './render'
import QuizPanel from '../components/quiz/QuizPanel'
import { LEVEL_KEY } from '../lib/learner/learnerLevel'
import { readRaw, writeRaw } from '../lib/store/stored'

describe('quiz', () => {
  it('answers a question', async () => {
    const { container } = renderScreen(<QuizPanel accent="#0a7" onProgress={() => {}} />)
    const options = await waitFor(() => {
      const found = [...container.querySelectorAll('button.option')]
      expect(found.length).toBeGreaterThan(1)
      return found
    }, { timeout: 3000 })
    // The way on is held in place before there is an answer, so arriving it
    // does not push the card's last row down.
    const next = screen.getByRole('button', { name: /Next word/, hidden: true })
    expect(next.disabled).toBe(true)
    fireEvent.click(options[0])
    expect(await screen.findByText(/^(Correct|Not this)$/)).toBeTruthy()
    expect(options.every((option) => option.disabled)).toBe(true)
    expect(screen.getByRole('button', { name: /Next word/ })).toBe(next)
    expect(next.disabled).toBe(false)
  })
})

describe('the quiz by level', () => {
  afterEach(() => localStorage.clear())

  it('gives a beginner the Basics: Grow\'s own cards, not word meanings', async () => {
    writeRaw(LEVEL_KEY, 'beginner')
    const { container } = renderScreen(<QuizPanel accent="#0a7" onProgress={() => {}} />, {
      routes: { 'GET /progress/summary': { items: [] } },
    })
    expect(await screen.findByText('means “the”', {}, { timeout: 3000 })).toBeTruthy()
    expect(container.querySelector('button.option')).toBeNull()
    // Grow's lesson is begun here too, so Grow does not open on the same first card again.
    expect(readRaw('basics-begun')).toBe('on')
  })

  it('keeps words for a learner past the basics', async () => {
    writeRaw(LEVEL_KEY, 'intermediate')
    const { container } = renderScreen(<QuizPanel accent="#0a7" onProgress={() => {}} />)
    await waitFor(() => expect(container.querySelectorAll('button.option').length).toBeGreaterThan(1), { timeout: 3000 })
    expect(screen.queryByText('means “the”')).toBeNull()
  })

  it('lets a set picked here win over the level', async () => {
    writeRaw(LEVEL_KEY, 'beginner')
    writeRaw('quiz-bank', 'quranic')
    const { container } = renderScreen(<QuizPanel accent="#0a7" onProgress={() => {}} />)
    await waitFor(() => expect(container.querySelectorAll('button.option').length).toBeGreaterThan(1), { timeout: 3000 })
  })
})
