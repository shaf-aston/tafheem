import { afterEach, describe, expect, it, vi } from 'vitest'

import { api } from '../../api'
import {
  answerInvite, deleteAccount, fetchAccount, fetchAccountNames, fetchCircle, fetchLeaderboard, fetchMemberOverview,
  fetchReviewItems, fetchSummary, forgetProgress, inviteMember, leaveFeedback, moveCircle, recordAttempt, removeMember, logIn, signUp,
} from './progress'

afterEach(() => vi.restoreAllMocks())

const refused = (status) => Object.assign(new Error('refused'), { response: { status } })

describe('filing an answer', () => {
  it('says so when it landed', async () => {
    vi.spyOn(api, 'post').mockResolvedValue({ status: 200 })
    const result = await recordAttempt({ module: 'quiz', item: 'train', correct: true })
    expect(result).toEqual({ saved: true, earned: 0 })
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
      module: 'quiz', item: 'train', correct: false, ms: 1200, context: { bank: 'everyday' }, tz: expect.any(Number),
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

describe('whose record', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    delete api.defaults.adapter
  })

  // Through axios itself, not a spy on api.get: the name is added on the way
  // out (api.js), so only a real request shows it.
  const sending = () => {
    const sent = []
    api.defaults.adapter = async (config) => {
      sent.push(config)
      return { data: { items: [], names: [] }, status: 200, statusText: 'OK', headers: {}, config }
    }
    return sent
  }

  it('every call carries the saved name', async () => {
    vi.stubGlobal('localStorage', { getItem: (k) => (k === 'profile' ? 'amina' : null) })
    const sent = sending()
    await fetchSummary('quiz')
    await fetchReviewItems('quiz')
    await recordAttempt({ module: 'quiz', item: 'train', correct: true })
    await leaveFeedback({ module: 'quiz', message: 'x' })
    await forgetProgress()
    await fetchAccount()
    await fetchLeaderboard('quiz')
    await deleteAccount()
    await fetchCircle(3)
    await inviteMember(3, 'bilal', 'member')
    await removeMember(3, 'bilal')
    expect(sent).toHaveLength(11)
    for (const config of sent) expect(config.headers.get('X-Tafheem-Profile')).toBe('amina')
  })

  it('sign-up and log-in send the name typed, not the one saved', async () => {
    vi.stubGlobal('localStorage', { getItem: (k) => (k === 'profile' ? 'amina' : null) })
    const sent = sending()
    await signUp('bilal', false)
    await logIn('bilal')
    expect(sent.map((config) => config.headers.get('X-Tafheem-Profile'))).toEqual(['bilal', 'bilal'])
    expect(JSON.parse(sent[0].data)).toEqual({ keep: false })
  })

  it('a guest sends no name', async () => {
    vi.stubGlobal('localStorage', { getItem: () => null })
    const sent = sending()
    await fetchSummary('quiz')
    expect(sent[0].headers.has('X-Tafheem-Profile')).toBe(false)
  })
})

describe('circles, and the log-in list', () => {
  it('invites by name in the body, in the circle named in the address', async () => {
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { id: 3 } })
    await inviteMember(3, 'amina', 'admin')
    expect(post.mock.calls[0][0]).toBe('/progress/circles/3/members')
    expect(post.mock.calls[0][1]).toEqual({ member: 'amina', role: 'admin' })
  })

  it('moves a circle by putting its new parent, or null, at its parent address', async () => {
    const put = vi.spyOn(api, 'put').mockResolvedValue({ data: {} })
    await moveCircle(3, 7)
    await moveCircle(3, null)
    expect(put.mock.calls.map((call) => call[0])).toEqual(['/progress/circles/3/parent', '/progress/circles/3/parent'])
    expect(put.mock.calls.map((call) => call[1])).toEqual([{ parent: 7 }, { parent: null }])
  })

  it('answers an invite with accept or decline', async () => {
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: {} })
    await answerInvite(3, true)
    await answerInvite(3, false)
    expect(post.mock.calls.map((call) => call[0])).toEqual(['/progress/circles/3/accept', '/progress/circles/3/decline'])
  })

  it('escapes a member name that is Arabic or has spaces, in the address', async () => {
    const get = vi.spyOn(api, 'get').mockResolvedValue({ data: {} })
    const del = vi.spyOn(api, 'delete').mockResolvedValue({ data: {} })
    await fetchMemberOverview(3, 'عائشة b')
    await removeMember(3, 'عائشة b')
    const encoded = encodeURIComponent('عائشة b')
    expect(get.mock.calls[0][0]).toBe(`/progress/circles/3/members/${encoded}/overview`)
    expect(del.mock.calls[0][0]).toBe(`/progress/circles/3/members/${encoded}`)
  })

  it('asks for a circle ranking by circle', async () => {
    const get = vi.spyOn(api, 'get').mockResolvedValue({ data: {} })
    await fetchLeaderboard('quiz', 3)
    expect(get.mock.calls[0][1].params).toEqual({ module: 'quiz', circle: 3 })
  })

  it('throws when beta is over, so the log-in list just goes', async () => {
    vi.spyOn(api, 'get').mockRejectedValue(refused(404))
    await expect(fetchAccountNames()).rejects.toThrow()
  })
})
