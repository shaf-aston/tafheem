// @vitest-environment happy-dom
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import QuestionForm from './QuestionForm'

afterEach(cleanup)

describe('QuestionForm', () => {
  it('keeps the whole form on screen, with no pill standing in for it', () => {
    render(
      <QuestionForm accent="red">
        <label htmlFor="box">Word</label>
        <input id="box" defaultValue="كتب" />
      </QuestionForm>,
    )
    expect(screen.getByLabelText('Word')).toBeTruthy()
    expect(screen.queryByRole('button', { name: /Edit the question/ })).toBeNull()
    expect(document.querySelector('[inert]')).toBeNull()
  })

  it('hands its accent to what it holds', () => {
    render(<QuestionForm accent="red"><span>x</span></QuestionForm>)
    expect(document.querySelector('.question-form').style.getPropertyValue('--c')).toBe('red')
  })
})
