import { afterEach, describe, expect, it, vi } from 'vitest'

import { fetchReviewItems, fetchSummary, recordAttempt } from './progress'

afterEach(() => vi.unstubAllGlobals())

const answering = (response) => {
  const fetching = vi.fn().mockResolvedValue(response)
  vi.stubGlobal('fetch', fetching)
  return fetching
}

describe('filing an answer', () => {
  it('says so when it landed', async () => {
    answering({ ok: true })
    const result = await recordAttempt({ module: 'quiz', item: 'train', correct: true })
    expect(result).toEqual({ saved: true })
  })

  it('never throws when there is no backend, so the round carries on', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    await expect(recordAttempt({ module: 'quiz', item: 'train', correct: true }))
      .resolves.toEqual({ saved: false })
  })

  it('reports a refusal rather than swallowing it', async () => {
    // A silent false success is the worst case: a whole session saved nowhere,
    // and no way for the panel to say so on screen.
    answering({ ok: false, status: 422 })
    const result = await recordAttempt({ module: 'quiz', item: 'train', correct: true })
    expect(result).toEqual({ saved: false })
  })

  it('sends what the store needs, and never says whose record it is', async () => {
    const fetching = answering({ ok: true })
    await recordAttempt({
      module: 'quiz', item: 'train', correct: false, ms: 1200, context: { bank: 'everyday' },
    })
    const sent = JSON.parse(fetching.mock.calls[0][1].body)
    expect(sent).toEqual({
      module: 'quiz', item: 'train', correct: false, ms: 1200, context: { bank: 'everyday' },
    })
    expect(sent).not.toHaveProperty('user')
  })
})

describe('reading it back', () => {
  it('returns the items', async () => {
    answering({ ok: true, json: async () => ({ module: 'quiz', items: [{ item: 'train' }] }) })
    expect(await fetchSummary('quiz')).toEqual([{ item: 'train' }])
  })

  it('throws when it cannot be read, so the panel can say so', async () => {
    answering({ ok: false, status: 500 })
    await expect(fetchSummary('quiz')).rejects.toThrow()
    answering({ ok: false, status: 500 })
    await expect(fetchReviewItems('quiz')).rejects.toThrow()
  })

  it('escapes the module name it is given', async () => {
    const fetching = answering({ ok: true, json: async () => ({ items: [] }) })
    await fetchReviewItems('a b&c')
    expect(fetching.mock.calls[0][0]).toContain('module=a%20b%26c')
  })
})
