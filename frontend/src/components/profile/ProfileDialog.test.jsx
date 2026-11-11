// @vitest-environment happy-dom
// Logging in on a new device: the box asks for the recovery code only when the server says so, and the code
// that replaces it is shown before the page reloads as the account.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AxiosError } from 'axios'
import { fireEvent, screen, waitFor } from '@testing-library/react'

import { renderScreen } from '../../test/render'
import ProfileDialog from './ProfileDialog'

const refused = (config, status, detail) => {
  throw new AxiosError('refused', AxiosError.ERR_BAD_REQUEST, config, null,
    { status, statusText: 'Refused', data: { detail }, headers: {}, config })
}
// The last "Log in": the first is the switch between Log in and Sign up.
const submit = () => screen.getAllByRole('button', { name: 'Log in' }).at(-1)
const ACCOUNT = { name: 'amina', joined: '2026-01-01', answers: 3, public: true, proven: true }

describe('logging in with a recovery code', () => {
  let sent
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
    sent = []
    vi.stubGlobal('location', { ...window.location, reload: vi.fn() })
  })
  afterEach(() => vi.unstubAllGlobals())

  const routes = {
    'POST /progress/login': (config) => {
      const body = JSON.parse(config.data)
      sent.push(body)
      if (!body.code) return refused(config, 403, "Type this account's recovery code")
      if (body.code !== 'abcd-efgh-jkmn-pqrs') return refused(config, 403, "That recovery code is not this account's")
      return { ...ACCOUNT, recovery: 'NEW1-NEW2-NEW3-NEW4' }
    },
    'GET /progress/saved': { data: {} },
    'PUT /progress/saved': { data: {} },
  }

  it('asks for the code only when refused, then shows the next one before logging in', async () => {
    const onClose = vi.fn()
    renderScreen(<ProfileDialog onClose={onClose} />, { routes })
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'amina' } })
    expect(screen.queryByLabelText('Recovery code')).toBeNull()
    fireEvent.click(submit())

    expect((await screen.findByRole('alert')).textContent).toBe("Type this account's recovery code")
    const code = screen.getByLabelText('Recovery code')
    fireEvent.change(code, { target: { value: 'wrong' } })
    fireEvent.click(submit())
    expect((await screen.findByRole('alert')).textContent).toBe("That recovery code is not this account's")

    fireEvent.change(code, { target: { value: 'abcd-efgh-jkmn-pqrs' } })
    fireEvent.click(submit())
    expect((await screen.findByTestId('recovery-code')).textContent).toBe('NEW1-NEW2-NEW3-NEW4')
    expect(sent).toEqual([{ shows_code: true }, { shows_code: true, code: 'wrong' }, { shows_code: true, code: 'abcd-efgh-jkmn-pqrs' }])
    expect(location.reload).not.toHaveBeenCalled() // not until the code has been seen
    fireEvent.click(screen.getByRole('button', { name: /close/i, hidden: true }))
    expect(onClose).not.toHaveBeenCalled() // the sheet is held while the code shows: nothing closes it but saving

    fireEvent.click(screen.getByRole('button', { name: 'I have saved it' }))
    await waitFor(() => expect(location.reload).toHaveBeenCalledOnce())
    expect(localStorage.getItem('profile')).toBe('amina')
  })

  it('says why the page logged itself out, where the way back in is', async () => {
    sessionStorage.setItem('tafheem-logged-out', 'amina: Log in again on this device.')
    vi.resetModules()
    // A fresh page: the note is read once per load. The fake backend is the fresh page's too.
    const { default: Dialog } = await import('./ProfileDialog')
    const fresh = await import('../../test/render')
    fresh.renderScreen(<Dialog onClose={() => {}} />, { routes })
    expect(screen.getByRole('alert').textContent).toBe('amina: Log in again on this device.')
  })
})
