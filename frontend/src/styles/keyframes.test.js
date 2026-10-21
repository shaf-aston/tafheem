// The app has one way to fade or rise in: motion.css's fade-in, fade-out and
// rise-in, tuned per place with --fade-from, --rise-from, --rise-y and
// --rise-scale. A keyframe anywhere else that only moves opacity and
// translate/scale on its way to rest (or only fades to nothing) is a copy of
// those, and fails here. One-off moves (a drift, a marquee, a ring pulsing
// out, a badge floating up and away) end somewhere else and pass.
// Timing has one owner too: a literal Nms or cubic-bezier( in a stylesheet is
// a duration or curve the Animations setting and theme.json cannot reach.
import { readFileSync, readdirSync } from 'node:fs'
import { join, relative } from 'node:path'
import { describe, expect, it } from 'vitest'

const SRC = join(import.meta.dirname, '..')
const OWNER = 'styles/motion.css'

const sheets = (dir) => readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
  const path = join(dir, entry.name)
  if (entry.isDirectory()) return sheets(path)
  return entry.name.endsWith('.css') ? [path] : []
})

// '@keyframes name { ...frames... }', frames nested one level deep.
const keyframes = (css) => [...css.matchAll(/@keyframes\s+([\w-]+)\s*\{((?:[^{}]*\{[^{}]*\})*[^{}]*)\}/g)]
  .map(([, name, body]) => ({ name, body }))

const declarations = (frame) => [...frame.matchAll(/([\w-]+)\s*:\s*([^;}]+)/g)].map(([, property, value]) => [property, value.trim()])

const movesOnly = (pairs) => pairs.every(([property, value]) =>
  property === 'opacity' || (property === 'transform' && /^(none|((translate[XY]?|scale)\([^)]*\)\s*)+)$/.test(value)))

const atRest = (pairs) => pairs.every(([property, value]) =>
  (property === 'opacity' && value === '1') || (property === 'transform' && value === 'none'))

// A copy of an enter move ends at rest (or leaves the end to the element);
// a copy of fade-out only takes opacity to 0. Frames are 'from'/'to'/'n%'.
const isCopy = (body) => {
  const frames = Object.fromEntries([...body.matchAll(/([\w%,\s]+)\{([^{}]*)\}/g)]
    .map(([, at, frame]) => [at.trim(), declarations(frame)]))
  const all = Object.values(frames).flat()
  if (all.length === 0 || !movesOnly(all)) return false
  const end = frames.to ?? frames['100%']
  const middle = Object.keys(frames).some((at) => !['from', 'to', '0%', '100%'].includes(at))
  if (middle) return false
  if (!end) return true
  if (atRest(end)) return true
  return Object.keys(frames).length === 1 && end.length === 1 && end[0][0] === 'opacity' && end[0][1] === '0'
}

// Allowed: 0.01ms (the reduced-motion reset), 0ms, and the unit in '* 1ms'.
const literalTimes = (css) => {
  const bare = css.replace(/\/\*[\s\S]*?\*\//g, '')
  return bare.split('\n').flatMap((line, i) => {
    const bad = [...line.matchAll(/(\*\s*)?(?<![\w.-])(\d*\.?\d+)ms\b/g)]
      .filter(([, times, n]) => !(Number(n) === 0 || n === '0.01' || (times && Number(n) === 1)))
    return bad.length || /cubic-bezier\(/.test(line) ? [i + 1] : []
  })
}

describe('keyframes', () => {
  it('durations and curves live in theme.json, not in a stylesheet', () => {
    const literals = sheets(SRC)
      .filter((path) => !['styles/motion.css'].includes(relative(SRC, path)) && !relative(SRC, path).startsWith('landing'))
      .flatMap((path) => literalTimes(readFileSync(path, 'utf8')).map((n) => `${relative(SRC, path)}:${n}`))
    expect(literals).toEqual([])
  })

  it('fade and rise live only in motion.css', () => {
    const copies = sheets(SRC)
      .filter((path) => relative(SRC, path) !== OWNER)
      .flatMap((path) => keyframes(readFileSync(path, 'utf8'))
        .filter(({ body }) => isCopy(body))
        .map(({ name }) => `${relative(SRC, path)}: ${name}`))
    expect(copies).toEqual([])
  })

  it('reads the keyframes it guards', () => {
    const own = keyframes(readFileSync(join(SRC, OWNER), 'utf8')).map(({ name }) => name)
    expect(own).toEqual(expect.arrayContaining(['fade-in', 'fade-out', 'rise-in']))
  })
})
