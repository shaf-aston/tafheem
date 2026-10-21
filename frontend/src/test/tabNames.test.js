// A tab's name is written once, in lib/tabs.js. Every panel title reads it
// (SectionHeader tab=), so a rename is one edit and cannot drift.
import { readdirSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const DIR = fileURLToPath(new URL('../components/', import.meta.url))
const panels = readdirSync(DIR).filter((f) => f.endsWith('.jsx'))
const headers = (src) => src.match(/<SectionHeader[\s\S]*?\/?>/g) ?? []

describe('tab names', () => {
  it('every panel header names its tab rather than spelling the name out', () => {
    const loose = panels.flatMap((f) => headers(readFileSync(DIR + f, 'utf8')).filter((h) => !/\btab=/.test(h)).map(() => f))
    expect(loose).toEqual([])
  })
})
