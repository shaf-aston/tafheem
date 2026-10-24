// Every world names the record it files under, once, in worlds.json; the code reads it from there, so a record's name
// can never drift between the world that files answers and the screens (Home, the level, the tabs) that read them.
import { describe, expect, it } from 'vitest'

import config from '../../config/worlds.json'
import levels from '../../config/levels.json'
import { moduleOf, worldOf } from './worlds'
import { MODULE as QUIZ_MODULE } from '../quiz/quizBanks'
import { MODULE as BASICS_MODULE } from './alifLam'

describe('worlds', () => {
  it('gives every world a record of its own, no two the same', () => {
    const modules = config.worlds.map((world) => world.module)
    expect(modules.every(Boolean)).toBe(true)
    expect(new Set(modules).size).toBe(modules.length)
  })

  it('files the Words world under the Quiz’s record, and the Basics under its lessons’', () => {
    expect(moduleOf('words')).toBe(QUIZ_MODULE)
    expect(moduleOf('basics')).toBe(BASICS_MODULE)
  })

  it('finds nothing for an unknown world', () => {
    expect(worldOf('nowhere')).toBeNull()
    expect(moduleOf('nowhere')).toBeNull()
  })

  it('proves each level with worlds that exist', () => {
    const proof = levels.levels.flatMap((level) => level.proof)
    expect(proof.length).toBeGreaterThan(0)
    expect(proof.every((id) => moduleOf(id))).toBe(true)
  })
})
