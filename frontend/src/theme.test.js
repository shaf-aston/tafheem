import { readdirSync, readFileSync } from 'node:fs'
import { join, relative } from 'node:path'
import { describe, expect, it } from 'vitest'

import theme from './theme.json'
import { THEME_NAMES, colorAt, colorFor, resolveTheme, tokenGroups } from './theme'

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
  })

  it('is handed to script as a pointer too, so it follows a look switch', () => {
    expect(colorFor('tab', 'nahw')).toBe('var(--palette-violet)')
    expect(colorFor('tab', 'nothing')).toBe('var(--palette-violet)')
    expect(colorAt('unit', 0)).toBe('var(--palette-orange)')
  })
})

describe('the looks', () => {
  const overrides = Object.entries(theme.themes).filter(([name, v]) => !name.startsWith('_') && typeof v === 'object')

  it('are the base plus a name', () => {
    expect(THEME_NAMES).toEqual(['dark', ...overrides.map(([name]) => name)])
  })

  it.each(overrides)('%s only changes tokens that exist', (name, look) => {
    const unknown = Object.entries(look)
      .filter(([group, values]) => !group.startsWith('_') && typeof values === 'object')
      .flatMap(([group, values]) =>
        Object.keys(values).filter((key) => !(key in (theme[group] ?? {}))).map((key) => `${group}.${key}`),
      )
    expect(unknown).toEqual([])
  })

  it.each(overrides)('%s repaints the whole palette', (name, look) => {
    const names = (palette) => Object.keys(palette).filter((key) => !key.startsWith('_')).sort()
    expect(names(look.palette)).toEqual(names(theme.palette))
  })

  it.each(overrides)('%s names the scheme the browser should match', (name, look) => {
    expect(['light', 'dark']).toContain(look.scheme)
  })

  it('write the same variables, only different values', () => {
    const names = (look) => tokenGroups(look).flatMap(([group, e]) => e.map(([key]) => `${group}.${key}`))
    expect(names('light')).toEqual(names('dark'))
  })

  it('send the device to light only when it says so', () => {
    expect(resolveTheme('system', true)).toBe('light')
    expect(resolveTheme('system', false)).toBe('dark')
    expect(resolveTheme('light')).toBe('light')
    expect(resolveTheme('nonsense')).toBe('dark')
  })
})

// Contrast is the one thing a colour swap breaks without anything crashing, so
// each look is held to it. Text tokens and every palette colour (worn as text,
// on the page and on a card) need 4.5:1; borders only 3:1.
const channel = (c) => ((c /= 255) <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)
const luminance = (hex) => {
  const n = parseInt(hex.slice(1), 16)
  return 0.2126 * channel(n >> 16) + 0.7152 * channel((n >> 8) & 255) + 0.0722 * channel(n & 255)
}
const contrast = (a, b) => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}
const lookOf = (name) => ({
  palette: Object.fromEntries(
    Object.entries({ ...theme.palette, ...theme.themes[name]?.palette }).filter(([key]) => !key.startsWith('_')),
  ),
  color: { ...theme.color, ...theme.themes[name]?.color },
})

describe.each(THEME_NAMES)('contrast in the %s look', (name) => {
  const { palette, color } = lookOf(name)
  const grounds = { page: color.bg, card: color.surface }

  it.each(['text', 'text-dim', 'text-faint'])('%s reads on the page and a card', (token) => {
    for (const [where, ground] of Object.entries(grounds)) {
      expect(contrast(color[token], ground), `${token} on ${where}`).toBeGreaterThanOrEqual(4.5)
    }
  })

  it('has palette colours that read as text on the page and a card', () => {
    const weak = Object.entries(palette).flatMap(([colour, hex]) =>
      Object.entries(grounds)
        .filter(([, ground]) => contrast(hex, ground) < 4.5)
        .map(([where, ground]) => `${colour} on ${where}: ${contrast(hex, ground).toFixed(2)}`),
    )
    expect(weak).toEqual([])
  })

  it('has a border that can be seen on a card', () => {
    expect(contrast(color['border-hi'], color.surface)).toBeGreaterThanOrEqual(1.5)
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
  'styles/motion.css': 1,
  'components/ui/ShowRest.jsx': 2,
  'styles/pbs.css': 1,
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
