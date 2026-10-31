// @vitest-environment happy-dom
// Answering for real: typing or arranging, then Check (or Enter), marks the answer given.
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { afterEach, describe, expect, it, vi } from 'vitest'

import ExerciseHost from './ExerciseHost'

afterEach(cleanup)
// An answer is filed with the server; here there is none to reach.
vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response('{}'))))

const typed = { id: 'u.l.reply.01', type: 'reply', prompt: 'Say hello', answer: 'مرحبا', accepted: ['مرحبا', 'marhaba'] }
const arranged = { id: 'u.l.reorder.01', type: 'reorder', prompt: 'Put it in order', answer: 'من أين أنت', accepted: ['من أين أنت'], words: ['أين', 'من', 'أنت'] }
const host = (exercise, onDone) => render(
  <QueryClientProvider client={new QueryClient()}><ExerciseHost exercise={exercise} onDone={onDone} /></QueryClientProvider>,
)

describe('ExerciseHost checking', () => {
  it('marks a typed answer right when Check is pressed', () => {
    const onDone = vi.fn()
    host(typed, onDone)
    fireEvent.change(screen.getByLabelText('Your answer'), { target: { value: 'marhaba' } })
    fireEvent.click(screen.getByRole('button', { name: 'Check' }))
    expect(onDone).toHaveBeenCalledWith(true, 'marhaba')
  })

  it('marks a typed answer wrong, and Enter checks it too', () => {
    const onDone = vi.fn()
    host(typed, onDone)
    const box = screen.getByLabelText('Your answer')
    fireEvent.change(box, { target: { value: 'xyz' } })
    fireEvent.keyDown(box, { key: 'Enter' })
    expect(onDone).toHaveBeenCalledWith(false, 'xyz')
    expect(screen.getByText(/The natural answer is/)).toBeTruthy()
  })

  it('checks an arranged answer', () => {
    const onDone = vi.fn()
    host(arranged, onDone)
    for (const word of ['من', 'أين', 'أنت']) fireEvent.click(screen.getAllByRole('button', { name: word })[0])
    fireEvent.click(screen.getByRole('button', { name: 'Check' }))
    expect(onDone).toHaveBeenCalledWith(true, ['من', 'أين', 'أنت'])
  })
})
