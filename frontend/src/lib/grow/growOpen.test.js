import { describe, expect, it } from 'vitest'

import { growOpen } from './growOpen'
import { WORLDS } from './worlds'

describe('growOpen', () => {
  it('fetches ahead every live world\'s items and record, and the XP, under the keys the hooks read', async () => {
    const keys = []
    await growOpen({ prefetchQuery: (query) => { keys.push(JSON.stringify(query.queryKey)) } })
    for (const world of WORLDS.filter((each) => each.live)) {
      expect(keys).toContain(JSON.stringify(['grow-source', world.id]))
      if (world.module) expect(keys.some((key) => key.includes(`"summary","${world.module}"`))).toBe(true)
    }
    expect(keys.some((key) => key.startsWith('["rewards"'))).toBe(true)
  })
})
