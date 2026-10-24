// A tab's name is written once, in lib/nav/tabs.js. Every panel title reads it
// (SectionHeader tab=), so a rename is one edit and cannot drift.
import { readdirSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

// Each tab's panel is components/<feature>/<Feature>Panel.jsx (lib/nav/tabs.js).
const DIR = fileURLToPath(new URL('../components/', import.meta.url))
const panels = readdirSync(DIR, { withFileTypes: true })
  .filter((d) => d.isDirectory())
  .flatMap((d) => readdirSync(DIR + d.name).filter((f) => f.endsWith('Panel.jsx')).map((f) => `${d.name}/${f}`))
const headers = (src) => src.match(/<SectionHeader[\s\S]*?\/?>/g) ?? []

describe('tab names', () => {
  it('every panel header names its tab rather than spelling the name out', () => {
    const loose = panels.flatMap((f) => headers(readFileSync(DIR + f, 'utf8')).filter((h) => !/\btab=/.test(h)).map(() => f))
    expect(loose).toEqual([])
  })
})
