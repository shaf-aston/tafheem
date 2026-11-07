// @vitest-environment happy-dom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import Tucked from './Tucked'

afterEach(cleanup)

const form = (answer, query = 'كتب') => (
  <Tucked answer={answer} query={query}>
    <label htmlFor="box">Word</label>
    <input id="box" defaultValue={query} />
  </Tucked>
)

const pill = () => screen.queryByRole('button', { name: /^Edit the question/ })
const folded = () => document.querySelector('.tucked-form').hasAttribute('inert')

describe('Tucked', () => {
  it('hands the focus to the pill when it folds under the cursor', () => {
    const { rerender } = render(form(null))
    screen.getByRole('textbox').focus()
    rerender(form({ hits: [] }))
    expect(document.activeElement).toBe(pill())
  })

  it('shows the whole form until there is an answer', () => {
    render(form(null))
    expect(pill()).toBeNull()
    expect(folded()).toBe(false)
  })

  it('folds into a pill naming the question once the answer is up', () => {
    render(form({ hits: [] }))
    expect(pill().getAttribute('aria-label')).toBe('Edit the question: كتب')
    expect(pill().getAttribute('aria-expanded')).toBe('false')
    expect(folded()).toBe(true)
  })

  it('stays open with nothing asked, so an empty box never folds', () => {
    render(form({ hits: [] }, '  '))
    expect(pill()).toBeNull()
  })

  it('opens again from the pill, with the cursor in the box', () => {
    render(form({ hits: [] }))
    fireEvent.click(pill())
    expect(pill()).toBeNull()
    expect(folded()).toBe(false)
    expect(document.activeElement).toBe(screen.getByLabelText('Word'))
  })

  it('folds again for the next answer, and not before', () => {
    const first = { hits: [1] }
    const { rerender } = render(form(first))
    fireEvent.click(pill())
    rerender(form(first))
    expect(pill()).toBeNull()
    rerender(form({ hits: [2] }))
    expect(pill()).not.toBeNull()
  })
})
