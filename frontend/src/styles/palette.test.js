// Every colour comes from theme.json (CORE-FLOW.md). A hex, rgb(a) or hsl(a)
// written into a stylesheet or component is a colour that no look can change,
// so it fails here with file:line. The allowlist is explicit: each entry names
// the file, the line's pattern and why a literal is right there.
import { readFileSync, readdirSync } from 'node:fs'
import { join, relative } from 'node:path'
import { describe, expect, it } from 'vitest'

const SRC = join(import.meta.dirname, '..')
const LITERAL = /(?<!&)#[0-9a-f]{3,8}\b|rgba?\(|hsla?\(/i
const SKIP = [/^theme\.json$/, /^landing\//, /\.test\./, /^styles\/motion\.css$/, /\.(json|svg|png)$/]
const ALLOWED = [
  { file: /\.jsx?$|\.css$/, line: /(mask|soft-edge)/i, why: 'a mask uses #000 (also the --soft-edge-* mask variables) for its alpha channel only, never as a colour on screen' },
  { file: /^styles\/timelines\.css$/, line: /hsl\(var\(/, why: 'hue/saturation/lightness come from theme.json timeline tokens' },
  { file: /^components\/shell\/Backdrop\.jsx$/, line: /rgba\(\$\{n >> 16\}/, why: 'a canvas gradient stop built from a token hex plus an alpha' },
]

const files = (dir) => readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
  const path = join(dir, entry.name)
  if (entry.isDirectory()) return files(path)
  return /\.(css|jsx?)$/.test(entry.name) ? [path] : []
})

describe('palette', () => {
  it('has no colour literal outside theme.json and the allowlist', () => {
    const found = files(SRC).flatMap((path) => {
      const file = relative(SRC, path)
      if (SKIP.some((pattern) => pattern.test(file))) return []
      return readFileSync(path, 'utf8').split('\n').flatMap((line, i) =>
        LITERAL.test(line) && !ALLOWED.some((a) => a.file.test(file) && a.line.test(line)) ? [`${file}:${i + 1}: ${line.trim().slice(0, 80)}`] : [])
    })
    expect(found).toEqual([])
  })
})
