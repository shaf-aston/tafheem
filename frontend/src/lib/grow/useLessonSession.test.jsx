// @vitest-environment happy-dom
// One lesson session for Grow and the Quiz's Basics: dealt once from a caught-up record, held while played, and the
// world's record re-read once it is left, before the next lesson is dealt.
import { afterEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, renderHook } from '@testing-library/react'

import { useLessonSession } from './useLessonSession'

afterEach(cleanup)

// A world as the session sees one; `refresh` resolves when `settle()` is called.
function fakeWorld(id, { dealable = true, behind = false } = {}) {
  let settle
  const world = {
    id,
    dealable,
    behind,
    dealt: 0,
    began: vi.fn(),
    refresh: vi.fn(() => new Promise((resolve) => { settle = resolve })),
    settle: () => act(async () => settle()),
  }
  return world
}

function session(worlds, first) {
  const byId = (id) => worlds[id]
  const deal = (world) => { world.dealt += 1; return 'cards' in world ? world.cards : [`${world.id}-${world.dealt}`] }
  return renderHook(({ playing }) => useLessonSession(byId, playing, deal), { initialProps: { playing: first } })
}

describe('useLessonSession', () => {
  it('deals once the world can, and holds the cards while played', () => {
    const basics = fakeWorld('basics', { dealable: false })
    const { result, rerender } = session({ basics }, { world: 'basics', key: 0 })
    expect(result.current).toBeNull()
    expect(basics.began).not.toHaveBeenCalled()
    basics.dealable = true
    rerender({ playing: { world: 'basics', key: 0 } })
    expect(result.current).toEqual(['basics-1'])
    rerender({ playing: { world: 'basics', key: 0 } })
    expect(result.current).toEqual(['basics-1'])
    expect(basics.dealt).toBe(1)
    expect(basics.began).toHaveBeenCalledTimes(1)
  })

  it('gives [] for nothing to deal (no cards, or no such lesson), without beginning the world', () => {
    for (const cards of [[], null]) {
      const basics = fakeWorld('basics')
      basics.cards = cards
      const { result } = session({ basics }, { world: 'basics', key: 0 })
      expect(result.current).toEqual([])
      expect(basics.began).not.toHaveBeenCalled()
    }
  })

  it('re-reads the left world and waits for it before dealing the next lesson', async () => {
    const basics = fakeWorld('basics')
    const words = fakeWorld('words')
    const { result, rerender } = session({ basics, words }, { world: 'basics', key: 'a' })
    expect(result.current).toEqual(['basics-1'])
    rerender({ playing: { world: 'words', key: 'b' } })
    expect(basics.refresh).toHaveBeenCalledTimes(1)
    expect(words.refresh).not.toHaveBeenCalled()
    expect(result.current).toBeNull()
    expect(words.dealt).toBe(0)
    await basics.settle()
    expect(result.current).toEqual(['words-1'])
  })

  it('re-reads on leaving for no lesson, and deals afresh when the same lesson is started again', async () => {
    const basics = fakeWorld('basics')
    const { result, rerender } = session({ basics }, { world: 'basics', key: 'a' })
    rerender({ playing: null })
    expect(result.current).toBeNull()
    expect(basics.refresh).toHaveBeenCalledTimes(1)
    await basics.settle()
    rerender({ playing: { world: 'basics', key: 'a' } })
    expect(result.current).toEqual(['basics-2'])
  })

  it('does not re-read a world whose lesson had nothing in it', () => {
    const basics = fakeWorld('basics')
    basics.cards = []
    const { rerender } = session({ basics }, { world: 'basics', key: 'a' })
    rerender({ playing: null })
    expect(basics.refresh).not.toHaveBeenCalled()
  })

  it('catches up a record left behind by answers elsewhere before dealing', () => {
    const basics = fakeWorld('basics', { dealable: false, behind: true })
    const { result, rerender } = session({ basics }, { world: 'basics', key: 0 })
    expect(basics.refresh).toHaveBeenCalledTimes(1)
    expect(result.current).toBeNull()
    Object.assign(basics, { behind: false, dealable: true })
    rerender({ playing: { world: 'basics', key: 0 } })
    expect(result.current).toEqual(['basics-1'])
    expect(basics.refresh).toHaveBeenCalledTimes(1)
  })

  it('catches up a record that falls behind while the lesson waits to be dealt', () => {
    const basics = fakeWorld('basics', { dealable: false })
    const { rerender } = session({ basics }, { world: 'basics', key: 0 })
    expect(basics.refresh).not.toHaveBeenCalled()
    basics.behind = true
    rerender({ playing: { world: 'basics', key: 0 } })
    expect(basics.refresh).toHaveBeenCalledTimes(1)
  })

  it('leaves the record alone while a lesson is played, however far behind its answers put it', () => {
    const basics = fakeWorld('basics')
    const { result, rerender } = session({ basics }, { world: 'basics', key: 0 })
    Object.assign(basics, { behind: true, dealable: false })
    rerender({ playing: { world: 'basics', key: 0 } })
    expect(result.current).toEqual(['basics-1'])
    expect(basics.refresh).not.toHaveBeenCalled()
  })

  it('begins only a world that keeps "begun"', () => {
    const words = fakeWorld('words')
    delete words.began
    const { result } = session({ words }, { world: 'words', key: 0 })
    expect(result.current).toEqual(['words-1'])
  })
})
