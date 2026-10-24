/**
 * Draws src/lib/colloquial/countryFlags.json: the flag of every country a dialect is
 * spoken in (backend/data/colloquial/dialects.json), for the dialect cards
 * (components/colloquial/CountryMap.jsx, CountryIcons).
 *
 * Run once; the output is committed and the app needs none of this:
 *
 *   npm i --no-save country-flag-icons@1.6.20
 *   node scripts/countryFlags.mjs
 *
 * The flags are country-flag-icons' 3:2 SVGs (MIT).
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const flags = require('country-flag-icons/string/3x2')
const { dialects } = JSON.parse(readFileSync(new URL('../../backend/data/colloquial/dialects.json', import.meta.url), 'utf8'))

const out = {}
for (const code of [...new Set(dialects.flatMap((d) => d.countries))].sort()) {
  if (!flags[code]) throw new Error(`No flag for ${code}`)
  out[code] = flags[code]
}
const file = new URL('../src/lib/colloquial/countryFlags.json', import.meta.url)
writeFileSync(file, JSON.stringify({ _about: 'country-flag-icons 3:2 flags (MIT), copied by scripts/countryFlags.mjs. Do not edit by hand.', flags: out }) + '\n')
console.log(Object.keys(out).length, 'flags,', readFileSync(file).length, 'bytes')
