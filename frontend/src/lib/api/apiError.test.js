import { describe, expect, it } from 'vitest'

import { retryServerErrors, smartError } from './apiError'

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

  it('names the backend when there was no response at all', () => {
    expect(smartError({ code: 'ERR_NETWORK' })).toMatch(/reach the backend/)
  })
})

describe('retryServerErrors', () => {
  const once = retryServerErrors(1)

  it('tries a server failure or a lost connection again, up to the count', () => {
    expect(once(0, failure(502))).toBe(true)
    expect(once(0, { code: 'ERR_NETWORK' })).toBe(true)
    expect(once(1, failure(502))).toBe(false)
  })

  // A model route counts every ask against the reader's share, refused or not.
  it('never asks again after a refusal', () => {
    for (const status of [400, 404, 422, 429]) expect(once(0, failure(status))).toBe(false)
  })
})
