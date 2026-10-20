import { readdirSync, readFileSync } from 'node:fs'
import { join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

import theme from './theme.json'
import { THEME_NAMES, colorAt, colorFor, resolveTheme, themeChoices, tokenGroups } from './theme'
import { contrast, oklch } from './lib/tone'

const SRC = fileURLToPath(new URL('.', import.meta.url))
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

const { looks, device, base } = theme.themes
// A look's tone is how it works out its palette, not a group it overrides.
const groupsOf = (look) =>
  Object.entries(look).filter(([key, value]) => !key.startsWith('_') && key !== 'tone' && typeof value === 'object')

describe('the looks', () => {
  it('are the ones theme.json lists, and include the base', () => {
    expect(THEME_NAMES).toEqual(Object.keys(looks))
    expect(THEME_NAMES).toContain(base)
  })

  it.each(Object.entries(looks))('%s says what Settings calls it and which scheme it is', (name, look) => {
    expect(look.label).toBeTruthy()
    expect(['light', 'dark']).toContain(look.scheme)
  })

  it.each(Object.entries(looks))('%s only changes tokens that exist', (name, look) => {
    const unknown = groupsOf(look).flatMap(([group, values]) =>
      Object.keys(values).filter((key) => !(key in (theme[group] ?? {}))).map((key) => `${group}.${key}`),
    )
    expect(unknown).toEqual([])
  })

  it('tone inside the comfort limits of their scheme', () => {
    for (const look of Object.values(looks)) {
      const tone = { ...theme.themes.tone, ...look.tone }
      const comfort = theme.themes.comfort[look.scheme]
      expect(tone['max-chroma']).toBeLessThanOrEqual(comfort['max-chroma'])
      expect(tone['max-lightness']).toBeLessThanOrEqual(comfort['max-lightness'] ?? 1)
    }
  })

  it('tone with the keys the base tone has', () => {
    for (const look of Object.values(looks).filter((look) => look.tone)) {
      expect(Object.keys(look.tone).filter((key) => !(key in theme.themes.tone))).toEqual([])
    }
  })

  it('write the same variables, only different values', () => {
    const names = (look) => tokenGroups(look).flatMap(([group, e]) => e.map(([key]) => `${group}.${key}`))
    for (const name of THEME_NAMES) expect(names(name)).toEqual(names(base))
  })

  it('are all offered to the reader, then the device', () => {
    expect(themeChoices().map(({ id }) => id)).toEqual([...THEME_NAMES, device.choice])
    expect(themeChoices().every(({ label }) => label)).toBe(true)
  })

  it('send the device to a look by its own answer, and anything unknown to the base', () => {
    expect(resolveTheme(device.choice, true)).toBe(device.light)
    expect(resolveTheme(device.choice, false)).toBe(device.dark)
    expect([device.light, device.dark]).toSatisfy((names) => names.every((name) => name in looks))
    expect(resolveTheme(THEME_NAMES.at(-1))).toBe(THEME_NAMES.at(-1))
    expect(resolveTheme('nonsense')).toBe(base)
  })
})

// Contrast is the one thing a colour swap breaks without anything crashing, so
// each look is held to it. Text tokens and every palette colour (worn as text,
// on the page, on a card, and on its own tint) need 4.5:1; borders only 3:1.
// A palette colour is also worn as text on a wash of itself (an error box, a
// tinted chip), which is a ground nearer to the text than the card is. The
// strongest wash in use is 14% (ui/Chip), so that is the one held to.
const WASH = 0.14
const washed = (hex, ground) => {
  const [a, b] = [hex, ground].map((value) => parseInt(value.slice(1), 16))
  const mixed = [16, 8, 0].map((shift) => Math.round(((a >> shift) & 255) * WASH + ((b >> shift) & 255) * (1 - WASH)))
  return `#${mixed.map((v) => v.toString(16).padStart(2, '0')).join('')}`
}
const lookOf = (name) => ({
  palette: Object.fromEntries(tokenGroups(name).find(([group]) => group === 'palette')[1]),
  color: { ...theme.color, ...looks[name]?.color },
})

describe.each(THEME_NAMES)('contrast in the %s look', (name) => {
  const { palette, color } = lookOf(name)
  const grounds = { page: color.bg, card: color.surface }
  // Pills and chips also sit on a raised card (a word in the i'raab view).
  const washGrounds = { ...grounds, raised: color['surface-hi'] }

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

  it('has palette colours that read on a wash of themselves', () => {
    const weak = Object.entries(palette).flatMap(([colour, hex]) =>
      Object.entries(washGrounds)
        .filter(([, ground]) => contrast(hex, washed(hex, ground)) < 4.5)
        .map(([where, ground]) => `${colour} on its wash over the ${where}: ${contrast(hex, washed(hex, ground)).toFixed(2)}`),
    )
    expect(weak).toEqual([])
  })

  // Words sit on tinted boxes too (an error, a role pill, a tinted chip), so a
  // text token has to read on the palette's washes over the page, a card and a
  // raised card. Midnight (the old dark base) predates this check, so its two quieter tokens
  // are held at what they measure today (they can only get better); a new look
  // gets the full 4.5.
  const BASE_FLOOR = { 'text-dim': 4.3, 'text-faint': 3.1 }
  it.each(['text', 'text-dim', 'text-faint'])('%s reads on a tinted card', (token) => {
    const floor = name === 'dark' ? BASE_FLOOR[token] ?? 4.5 : 4.5
    const worst = Math.min(...Object.values(palette).flatMap((hex) =>
      Object.values(washGrounds).map((ground) => contrast(color[token], washed(hex, ground)))))
    expect(worst).toBeGreaterThanOrEqual(floor)
  })

  it('has a border that can be seen on a card', () => {
    expect(contrast(color['border-hi'], color.surface)).toBeGreaterThanOrEqual(1.5)
  })

  // Too much is a fault too: glaring text, dazzling grounds, colours that vibrate.
  it('is easy on the eyes', () => {
    const comfort = theme.themes.comfort[looks[name].scheme]
    const brightest = Math.max(...Object.values(grounds).map((ground) => contrast(color.text, ground)))
    expect(brightest, 'text on its brightest ground').toBeLessThanOrEqual(comfort['text-max-contrast'])
    const loud = Object.entries(palette)
      .map(([colour, hex]) => [colour, oklch(hex)])
      .filter(([, [l, c]]) => c > comfort['max-chroma'] || l > (comfort['max-lightness'] ?? 1))
      .map(([colour, [l, c]]) => `${colour}: lightness ${l.toFixed(2)}, chroma ${c.toFixed(3)}`)
    expect(loud).toEqual([])
    const dazzling = Object.entries(washGrounds).filter(([, ground]) => oklch(ground)[0] > (comfort['max-ground-lightness'] ?? 1))
    expect(dazzling.map(([where]) => where)).toEqual([])
  })

  it('outlines a control and writes on a filled accent so both can be seen', () => {
    const faint = Object.entries(grounds).filter(([, ground]) => contrast(color['border-hi'], ground) < 3)
    expect(faint.map(([where]) => where), 'border-hi under 3:1').toEqual([])
    const unreadable = Object.entries(palette).filter(([, hex]) => contrast(color['on-accent'], hex) < 4.5)
    expect(unreadable.map(([colour]) => colour), 'on-accent under 4.5:1').toEqual([])
  })
})

// A look is one file. A new colour literal in a stylesheet or a component is the
// look leaking out of it again, so the count of lines carrying one may only fall.
// Lower a number when a file is cleaned; never raise one, add a token instead.
// A mask only reads the alpha of its colour (#000 there means "opaque"), so a
// line that is a mask is not a colour.
const LITERAL = /#[0-9a-f]{3}\b|#[0-9a-f]{6}\b|\brgba?\(|\bhsla?\(/i
const isMask = (line) => /mask|soft-edge/i.test(line)
const ALLOWED = {
  'landing/AyahDiagram.css': 1,
  'styles/timelines.css': 2,
  'styles/motion.css': 1,
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
        relative(SRC, path).replaceAll('\\', '/'),
        readFileSync(path, 'utf8').split('\n').filter((line) => LITERAL.test(line) && !isMask(line)).length,
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
