// @vitest-environment happy-dom
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

const leaveFeedback = vi.fn(async () => ({ saved: true }))
vi.mock('../../lib/learner/progress', () => ({ leaveFeedback: (note) => leaveFeedback(note) }))

import FooterNote from './FooterNote'

afterEach(() => { cleanup(); leaveFeedback.mockClear() })

const send = () => screen.getByRole('button', { name: 'Send' })
const type = (label, value) => fireEvent.change(screen.getByLabelText(label), { target: { value } })

describe('FooterNote', () => {
  it('sends a note, filed as the site from where it was written', async () => {
    render(<FooterNote where="dict" />)
    expect(send().disabled).toBe(true)
    type('Spotted a mistake or have an idea?', '  a typo in Lane  ')
    fireEvent.click(send())
    await screen.findByText('Thanks, your note is in.')
    expect(leaveFeedback).toHaveBeenCalledWith({ module: 'site', item: 'dict', message: 'a typo in Lane', email: undefined, updates: false })
  })

  it('holds the note while the email is half typed, and says what is missing', () => {
    render(<FooterNote where="dict" />)
    type('Spotted a mistake or have an idea?', 'idea')
    type('Email, if you’d like a reply', 'me@')
    expect(send().disabled).toBe(true)
    expect(screen.getByRole('alert').textContent).toMatch(/missing an @ or a domain/)
  })

  it('takes a request for updates alone: an email and the box, no message', async () => {
    render(<FooterNote where="landing" />)
    fireEvent.click(screen.getByRole('button', { name: 'Get updates by email' }))
    expect(screen.getByLabelText('Send me the occasional update').checked).toBe(true)
    expect(send().disabled).toBe(true) // updates, but nowhere to send them yet
    type('Email, if you’d like a reply', 'me@example.com')
    fireEvent.click(send())
    await screen.findByText('Thanks. Updates will go to me@example.com.')
    expect(leaveFeedback).toHaveBeenCalledWith({ module: 'site', item: 'landing', message: '', email: 'me@example.com', updates: true })
  })

  it('keeps what was written when it could not be sent', async () => {
    leaveFeedback.mockResolvedValueOnce({ saved: false })
    render(<FooterNote where="dict" />)
    type('Spotted a mistake or have an idea?', 'keep me')
    fireEvent.click(send())
    await waitFor(() => expect(screen.getByRole('alert').textContent).toMatch(/Couldn’t send/))
    expect(screen.getByLabelText('Spotted a mistake or have an idea?').value).toBe('keep me')
  })
})
