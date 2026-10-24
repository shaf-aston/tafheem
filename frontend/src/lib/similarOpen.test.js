import { describe, expect, it } from 'vitest'

import copy from '../config/similar.json'
import { similarOpen } from './similarOpen'

const groups = { groups: [{ pairs: [['2:35', '7:19'], ['7:161', '2:58']] }] }

// A stand-in query client: fetchQuery answers with the surah's groups, prefetchQuery notes the key.
const clientFor = (data = groups) => {
  const asked = []
  return {
    asked,
    fetchQuery: (q) => { asked.push(q.queryKey); return Promise.resolve(data) },
    prefetchQuery: (q) => { asked.push(q.queryKey); return Promise.resolve() },
  }
}

describe('similarOpen', () => {
  it('fetches the asked verse’s surah, then that verse’s pair', async () => {
    const client = clientFor()
    await similarOpen(client, '2:58')
    expect(client.asked).toEqual([['similar-surah', 2], ['similar', '2', '58']])
  })

  it('with no verse asked, the default surah and its first pair', async () => {
    const client = clientFor()
    await similarOpen(client, null)
    expect(client.asked[0]).toEqual(['similar-surah', copy['default-surah']])
  })

  it('a surah with no pairs asks for nothing more', async () => {
    const client = clientFor({ groups: [] })
    await similarOpen(client, '2:58')
    expect(client.asked).toEqual([['similar-surah', 2]])
  })
})
