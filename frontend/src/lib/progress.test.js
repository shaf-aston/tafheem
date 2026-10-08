import { afterEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api'
import {
  addMember, deleteAccount, fetchAccount, fetchAccountNames, fetchLeaderboard, fetchReviewItems, fetchSummary, fetchTeam, forgetProgress, leaveFeedback, logIn,
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
    await fetchTeam('quiz')
    await addMember('bilal', 'quiz')
    await removeMember('amina', 'bilal', 'quiz')
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
