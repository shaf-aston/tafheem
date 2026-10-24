// @vitest-environment happy-dom
// The one door for answers: filing re-reads the overview at once (so the level follows), and only marks the answered
// module's own views old, so a round or a lesson being played holds still until its screen calls `refresh`.
import { afterEach, describe, expect, it } from 'vitest'
import { act, fireEvent, screen, waitFor } from '@testing-library/react'
import { useQuery } from '@tanstack/react-query'

import { renderScreen, renderWithBackend } from '../../test/render'
import LevelSetting from '../../components/level/LevelSetting'
import { RULES } from './learnerLevel'
import { accountQuery, everyRanking, fileAnswer, leaderboardQuery, overviewQuery, reviewQuery, summaryQuery, useRecord } from './record'
import { forgetDevice, writeDevice } from '../store/stored'
import CONFIG from '../../config/profile.json'

const NAME = 'amina'
const ANSWER = { module: 'basics', item: 'al:kitab', correct: true, ms: 900 }

afterEach(() => {
  forgetDevice(CONFIG.storageKey)
  localStorage.clear()
})

// Every view of the record, each reading the store once per fetch; `count` is how often each path was asked.
function readEveryView({ saved = true } = {}) {
  const count = {}
  const answer = (path, data) => () => { count[path] = (count[path] ?? 0) + 1; return data }
  const routes = {
    'GET /progress/overview': answer('overview', { modules: [] }),
    'GET /progress/account': answer('account', { name: NAME }),
    'GET /progress/leaderboard': answer('leaderboard', { rows: [] }),
    'GET /progress/summary': (config) => answer(`summary ${config.params.module}`, { items: [] })(),
    'GET /progress/review': (config) => answer(`review ${config.params.module}`, { items: [] })(),
    ...(saved && { 'POST /progress/attempts': { earned: 2 } }),
  }
  const useViews = () => [
    useQuery(overviewQuery(NAME)), useQuery(accountQuery(NAME)), useQuery(leaderboardQuery('basics')),
    useQuery(summaryQuery('basics')), useQuery(reviewQuery('basics')), useQuery(summaryQuery('quiz')),
  ]
  const hook = renderWithBackend(() => ({ views: useViews(), record: useRecord() }), { routes })
  return { ...hook, count }
}

const allIn = async (result) => waitFor(() => expect(result.current.views.every((view) => view.isSuccess)).toBe(true))
const stale = (client, query) => client.getQueryState(query.queryKey).isInvalidated

describe('fileAnswer', () => {
  it('re-reads the overview at once and only marks the answered module and the figures old', async () => {
    const { result, client, count } = readEveryView()
    await allIn(result)
    const filed = await act(() => result.current.record.file(ANSWER))
    expect(filed).toEqual({ saved: true, earned: 2 })
    await waitFor(() => expect(count.overview).toBe(2))
    // Old, not re-read: the lesson holding them is not re-planned under the player.
    for (const query of [summaryQuery('basics'), reviewQuery('basics'), leaderboardQuery('basics'), accountQuery(NAME)]) {
      expect(stale(client, query)).toBe(true)
    }
    expect(count).toMatchObject({ account: 1, leaderboard: 1, 'summary basics': 1, 'review basics': 1 })
    // Another module's record is untouched.
    expect(stale(client, summaryQuery('quiz'))).toBe(false)
  })

  it('changes nothing when the answer did not land', async () => {
    const { result, client, count } = readEveryView({ saved: false })
    await allIn(result)
    expect(await act(() => result.current.record.file(ANSWER))).toEqual({ saved: false })
    expect(count.overview).toBe(1)
    expect(stale(client, summaryQuery('basics'))).toBe(false)
    expect(stale(client, overviewQuery(NAME))).toBe(false)
  })

  it('works on a bare client, outside a screen', async () => {
    const { client } = renderWithBackend(() => null, { routes: { 'POST /progress/attempts': {} } })
    expect(await fileAnswer(client, ANSWER)).toEqual({ saved: true, earned: 0 })
  })
})

describe('refresh', () => {
  it("re-reads one module's summary and review now, and nothing else", async () => {
    const { result, count } = readEveryView()
    await allIn(result)
    await act(() => result.current.record.refresh('basics'))
    expect(count).toMatchObject({ 'summary basics': 2, 'review basics': 2, 'summary quiz': 1, overview: 1, leaderboard: 1 })
  })
})

describe('everyRanking', () => {
  it("names every module's ranking and no other view", async () => {
    const { result, client } = readEveryView()
    await allIn(result)
    await act(() => client.invalidateQueries({ ...everyRanking, refetchType: 'none' }))
    expect(stale(client, leaderboardQuery('basics'))).toBe(true)
    expect(stale(client, summaryQuery('basics'))).toBe(false)
  })
})

describe('Your Arabic, after answers', () => {
  it('settles without a reload once enough answers are filed', async () => {
    writeDevice(CONFIG.storageKey, NAME)
    let answers = RULES.minAnswers - 1
    const row = () => ({ module: 'basics', attempts: answers, correct: answers, learnt: 0, lastAt: '2026-10-23T00:00:00Z' })
    function Screen() {
      const { file } = useRecord()
      return (
        <>
          <LevelSetting />
          <button type="button" onClick={() => file(ANSWER)}>Answer</button>
        </>
      )
    }
    renderScreen(<Screen />, {
      routes: {
        'GET /progress/overview': () => ({ modules: [row()] }),
        'POST /progress/attempts': () => { answers += 1; return { earned: 1 } },
      },
    })
    await screen.findByRole('button', { name: 'Advanced' })
    fireEvent.click(screen.getByRole('button', { name: 'Answer' }))
    expect(await screen.findByText(/Set by your answers: 100% right over 30 Basics answers/)).toBeTruthy()
  })
})
