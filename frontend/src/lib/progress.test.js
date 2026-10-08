import { afterEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api'
import {
  addMember, deleteAccount, fetchAccount, fetchAccountNames, fetchLeaderboard, fetchReviewItems, fetchSummary, forgetProgress, leaveFeedback, logIn,
  recordAttempt, removeMember, signUp,
} from './progress'

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

  it('sends what the store needs, with the name in a header and not the body', async () => {
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
    expect(getting).toHaveBeenCalledWith('/progress/review', { params: { module: 'a b&c' }, headers: {} })
  })
})

describe('whose record', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('every call carries the saved name', async () => {
    vi.stubGlobal('localStorage', { getItem: (k) => (k === 'profile' ? 'amina' : null) })
    const getting = vi.spyOn(api, 'get').mockResolvedValue({ data: { items: [] } })
    const posting = vi.spyOn(api, 'post').mockResolvedValue({ status: 200, data: { name: 'amina', moved: 0 } })
    const deleting = vi.spyOn(api, 'delete').mockResolvedValue({ status: 200 })
    await fetchSummary('quiz')
    await fetchReviewItems('quiz')
    await recordAttempt({ module: 'quiz', item: 'train', correct: true })
    await leaveFeedback({ module: 'quiz', message: 'x' })
    await forgetProgress()
    await signUp('amina', false)
    await logIn('amina')
    await fetchAccount()
    await fetchLeaderboard('quiz')
    await deleteAccount()
    const sent = { headers: { 'X-Tafheem-Profile': 'amina' } }
    for (const call of getting.mock.calls) expect(call[1]).toMatchObject(sent)
    for (const call of posting.mock.calls) expect(call[2]).toEqual(sent)
    for (const call of deleting.mock.calls) expect(call[1]).toEqual(sent)
    expect(getting).toHaveBeenCalledTimes(4)
    expect(posting).toHaveBeenCalledTimes(4)
    expect(posting.mock.calls[2]).toEqual(['/progress/signup', { keep: false }, sent])
    expect(posting.mock.calls[3]).toEqual(['/progress/login', {}, sent])
    expect(deleting.mock.calls[1][0]).toBe('/progress/account')
  })
})

describe('teams', () => {
  it('adds a member as the logged-in name and hands back the new team', async () => {
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { tree: { name: 'coach' }, teams: [] } })
    await expect(addMember('amina', 'quiz')).resolves.toEqual({ tree: { name: 'coach' }, teams: [] })
    expect(post.mock.calls[0][1]).toEqual({ member: 'amina' })
    expect(post.mock.calls[0][2].params).toEqual({ module: 'quiz' })
  })

  it('says who parts from whom', async () => {
    const del = vi.spyOn(api, 'delete').mockResolvedValue({ data: {} })
    await removeMember('coach', 'amina', 'quiz')
    expect(del.mock.calls[0][1].params).toEqual({ team: 'coach', member: 'amina', module: 'quiz' })
  })

  it('throws when beta is over, so the log-in list just goes', async () => {
    vi.spyOn(api, 'get').mockRejectedValue(refused(404))
    await expect(fetchAccountNames()).rejects.toThrow()
  })
})
