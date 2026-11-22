import { describe, expect, it, vi } from 'vitest'

import { errorMessage, retryServerErrors, smartError } from './apiError'

const failure = (status, detail) => ({ response: { status, data: detail ? { detail } : {} } })

describe('smartError', () => {
  it('prefers what the server actually said', () => {
    expect(smartError(failure(404, 'The book prints no entry under those letters.')))
      .toBe('The book prints no entry under those letters.')
  })

  // 503 is not only "still starting". It is also "this part is switched off",
  // and the server names which part, telling the reader to wait instead sends
  // them to watch a startup that finished long ago.
  it('says why a service is unavailable rather than guessing at startup', () => {
    expect(smartError(failure(503, 'No AI is reachable, so the entry cannot be put into English.')))
      .toBe('No AI is reachable, so the entry cannot be put into English.')
  })

  it('still explains a bare 503 that came with no reason', () => {
    expect(smartError(failure(503))).toMatch(/starting up/)
  })

  it('says the server could not be reached when there was no response at all, with no command for a visitor', () => {
    expect(smartError({ code: 'ERR_NETWORK' })).toMatch(/reach the server/)
    expect(smartError({ code: 'ERR_NETWORK' })).not.toMatch(/uvicorn/)
  })

  it("blames no signal, not the server, when the phone has none", () => {
    vi.stubGlobal('navigator', { onLine: false })
    expect(smartError({ code: 'ERR_NETWORK' })).toMatch(/No signal/)
    expect(errorMessage(new Error('Network Error'))).toMatch(/No signal/)
    vi.unstubAllGlobals()
  })
})

describe('errorMessage', () => {
  it("never shows a bare 'Network Error'", () => {
    expect(errorMessage(new Error('Network Error'))).toMatch(/reach the server/)
  })

  it('says plainly when the host could not reach the server, not "status code 502"', () => {
    expect(errorMessage(failure(502))).toMatch(/reach the server/)
    expect(smartError(failure(504))).toMatch(/reach the server/)
  })

  it('keeps what the server said, and other messages as they are', () => {
    expect(errorMessage(failure(422, 'Not Arabic.'))).toBe('Not Arabic.')
    expect(errorMessage(new Error('Bad JSON'))).toBe('Bad JSON')
  })
})

describe('retryServerErrors', () => {
  const once = retryServerErrors(1)

  it('tries a server failure or a lost connection again, up to the count', () => {
    expect(once(0, failure(500))).toBe(true)
    expect(once(0, { code: 'ERR_NETWORK' })).toBe(true)
    expect(once(1, failure(500))).toBe(false)
  })

  // The host already waited ~30 s for the server: asking again only waits another 30 s.
  it('not when the host could not reach the server', () => {
    expect(once(0, failure(502))).toBe(false)
    expect(once(0, failure(504))).toBe(false)
  })

  // A model route counts every ask against the reader's share, refused or not.
  it('never asks again after a refusal', () => {
    for (const status of [400, 404, 422, 429]) expect(once(0, failure(status))).toBe(false)
  })
})
