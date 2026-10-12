import { readdirSync, readFileSync } from 'node:fs'
import { join, relative } from 'node:path'
import { describe, expect, it } from 'vitest'

import theme from './theme.json'
import { colorAt, colorFor, tokenGroups } from './theme'

const SRC = new URL('.', import.meta.url).pathname
const HEX = /^#[0-9a-f]{6}$/i

const tokens = Object.entries(theme).filter(([group, values]) => !group.startsWith('_') && typeof values === 'object')
const entries = tokens.flatMap(([group, values]) =>
  Object.entries(values).filter(([key]) => !key.startsWith('_')).map(([key, value]) => ({ group, key, value })),
)

describe('the palette', () => {
  it('has every @name a token points at', () => {
    const missing = entries
      .filter(({ value }) => typeof value === 'string' && value.startsWith('@'))
      .filter(({ value }) => !(value.slice(1) in theme.palette))
    expect(missing).toEqual([])
  })

  it('is the only place a palette colour is written out', () => {
    const palette = new Set(Object.values(theme.palette).map((hex) => hex.toLowerCase()))
    const repeats = entries
      .filter(({ group }) => group !== 'palette')
      .filter(({ value }) => HEX.test(value) && palette.has(value.toLowerCase()))
      .map(({ group, key }) => `${group}.${key}`)
    expect(repeats).toEqual([])
  })

  it('reaches CSS as a pointer, and script as the colour', () => {
    const css = Object.fromEntries(tokenGroups().find(([group]) => group === 'tab')[1])
    expect(css.nahw).toBe('var(--palette-violet)')
    expect(colorFor('tab', 'nahw')).toBe(theme.palette.violet)
    expect(colorFor('tab', 'nothing')).toBe(theme.palette.violet)
    expect(colorAt('unit', 0)).toBe(theme.palette.orange)
  })
})

// A look is one file. A new colour literal in a stylesheet or a component is the
// look leaking out of it again, so the count of lines carrying one may only fall.
// Lower a number when a file is cleaned; never raise one, add a token instead.
const LITERAL = /#[0-9a-f]{3}\b|#[0-9a-f]{6}\b|\brgba?\(|\bhsla?\(/i
const ALLOWED = {
  'landing/landing.css': 20,
  'landing/AyahDiagram.css': 10,
  'lib/pbsData.js': 10,
  'styles/components.css': 5,
  'styles/timelines.css': 3,
  'styles/motion.css': 2,
  'components/ui/ShowRest.jsx': 2,
  'styles/pbs.css': 1,
  'styles/layers.css': 1,
  'styles/command.css': 1,
  'components/shell/Backdrop.jsx': 1,
}

function sources(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name)
    if (entry.isDirectory()) return sources(path)
    return /\.(css|jsx?)$/.test(entry.name) && !/\.test\./.test(entry.name) ? [path] : []
  })
}

describe('colour literals outside theme.json', () => {
  const found = Object.fromEntries(
    sources(SRC)
      .map((path) => [
        relative(SRC, path),
        readFileSync(path, 'utf8').split('\n').filter((line) => LITERAL.test(line)).length,
      ])
      .filter(([, count]) => count > 0),
  )

  it('are no more than the ones already there', () => {
    const grown = Object.entries(found)
      .filter(([file, count]) => count > (ALLOWED[file] ?? 0))
      .map(([file, count]) => `${file}: ${count} lines, ${ALLOWED[file] ?? 0} allowed`)
    expect(grown).toEqual([])
  })

  it('keep the allowance honest: a cleaned file is lowered here', () => {
    const slack = Object.entries(ALLOWED)
      .filter(([file, count]) => (found[file] ?? 0) < count)
      .map(([file, count]) => `${file}: ${found[file] ?? 0} lines, ${count} allowed`)
    expect(slack).toEqual([])
  })
})
