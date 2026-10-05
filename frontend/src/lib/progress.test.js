import { afterEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api'
import { fetchReviewItems, fetchSummary, recordAttempt } from './progress'

afterEach(() => vi.restoreAllMocks())

const refused = (status) => Object.assign(new Error('refused'), { response: { status } })

describe('filing an answer', () => {
  it('says so when it landed', async () => {
    vi.spyOn(api, 'post').mockResolvedValue({ status: 200 })
    const result = await recordAttempt({ module: 'quiz', item: 'train', correct: true })
    expect(result).toEqual({ saved: true })
  })

  it('never throws when there is no backend, so the round carries on', async () => {
    vi.spyOn(api, 'post').mockRejectedValue(new Error('Network Error'))
    await expect(recordAttempt({ module: 'quiz', item: 'train', correct: true }))
      .resolves.toEqual({ saved: false })
  })

  it('reports a refusal rather than swallowing it', async () => {
    // A silent false success is the worst case: a whole session saved nowhere,
    // and no way for the panel to say so on screen.
    vi.spyOn(api, 'post').mockRejectedValue(refused(422))
    const result = await recordAttempt({ module: 'quiz', item: 'train', correct: true })
    expect(result).toEqual({ saved: false })
  })

  it('sends what the store needs, and never says whose record it is', async () => {
    const posting = vi.spyOn(api, 'post').mockResolvedValue({ status: 200 })
    await recordAttempt({
      module: 'quiz', item: 'train', correct: false, ms: 1200, context: { bank: 'everyday' },
    })
    const sent = posting.mock.calls[0][1]
    expect(sent).toEqual({
      module: 'quiz', item: 'train', correct: false, ms: 1200, context: { bank: 'everyday' },
    })
    expect(sent).not.toHaveProperty('user')
  })
})

describe('reading it back', () => {
  it('returns the items', async () => {
    vi.spyOn(api, 'get').mockResolvedValue({ data: { module: 'quiz', items: [{ item: 'train' }] } })
    expect(await fetchSummary('quiz')).toEqual([{ item: 'train' }])
  })

  it('throws with the status, so the panel can say why', async () => {
    vi.spyOn(api, 'get').mockRejectedValue(refused(500))
    await expect(fetchSummary('quiz')).rejects.toMatchObject({ response: { status: 500 } })
    await expect(fetchReviewItems('quiz')).rejects.toMatchObject({ response: { status: 500 } })
  })

  it('passes the module name as a parameter, so it is escaped', async () => {
    const getting = vi.spyOn(api, 'get').mockResolvedValue({ data: { items: [] } })
    await fetchReviewItems('a b&c')
    expect(getting).toHaveBeenCalledWith('/progress/review', { params: { module: 'a b&c' } })
  })
})
