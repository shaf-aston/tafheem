// @vitest-environment happy-dom
// The quiz's core loop on the real word banks: a question comes up, a pick
// gets a verdict on the option itself, and the options lock.
import { describe, expect, it } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'

import { renderScreen } from './render'
import QuizPanel from '../components/QuizPanel'

describe('quiz', () => {
  it('answers a question', async () => {
    const { container } = renderScreen(<QuizPanel accent="#0a7" onProgress={() => {}} />)
    const options = await waitFor(() => {
      const found = [...container.querySelectorAll('button.option')]
      expect(found.length).toBeGreaterThan(1)
      return found
    }, { timeout: 3000 })
    fireEvent.click(options[0])
    expect(await screen.findByText(/^(Correct|Not this)$/)).toBeTruthy()
    expect(options.every((option) => option.disabled)).toBe(true)
  })
})
