import { describe, expect, it } from 'vitest'
import { TOOLS } from './tools'

describe('TOOLS', () => {
  it('has unique ids, so no two buttons share a handler or a hint id', () => {
    expect(new Set(TOOLS.map((tool) => tool.id)).size).toBe(TOOLS.length)
  })
  it('places each tool on the bar or in More, and draws it', () => {
    for (const tool of TOOLS) {
      expect([undefined, 'more']).toContain(tool.phone)
      expect(tool.paths.length).toBeGreaterThan(0)
    }
  })
})
