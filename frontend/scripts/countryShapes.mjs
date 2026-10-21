/**
 * Draws src/data/countryShapes.json: a simplified outline of every country in
 * and around the Arab world, for the small maps on the Colloquial dialect cards
 * (components/ui/CountryMap.jsx).
 *
 * Run once; the output is committed and the app needs none of this:
 *
 *   npm i --no-save world-atlas@2 topojson-client@3 topojson-simplify@3
 *   node scripts/countryShapes.mjs
 *
 * The outlines are Natural Earth's 1:50m countries (public domain), through
 * world-atlas. Simplified as one topology, so neighbours keep sharing a border.
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { feature } from 'topojson-client'
import { presimplify, simplify, quantile } from 'topojson-simplify'

import { project } from '../src/lib/countryMap.js'

const require = createRequire(import.meta.url)
const world = JSON.parse(readFileSync(require.resolve('world-atlas/countries-50m.json'), 'utf8'))

// ISO 3166 numeric → alpha-2, for every country whose middle falls in the
// region below. The Arab League's 22, then the neighbours a map shows round them.
const ARAB = {
  '012': 'DZ', '048': 'BH', '174': 'KM', '262': 'DJ', '818': 'EG', '368': 'IQ', '400': 'JO', '414': 'KW',
  '422': 'LB', '434': 'LY', '478': 'MR', '504': 'MA', '512': 'OM', '275': 'PS', '634': 'QA', '682': 'SA',
  '706': 'SO', '729': 'SD', '760': 'SY', '788': 'TN', '784': 'AE', '887': 'YE',
}
const NEIGHBOURS = {
  '376': 'IL', '732': 'EH', '792': 'TR', '364': 'IR', '196': 'CY', '724': 'ES', '620': 'PT', '466': 'ML',
  '562': 'NE', '148': 'TD', '728': 'SS', '231': 'ET', '232': 'ER', '686': 'SN', '270': 'GM', '624': 'GW',
  '324': 'GN', '854': 'BF', '566': 'NG', '120': 'CM', '140': 'CF', '051': 'AM', '031': 'AZ', '268': 'GE',
  '004': 'AF', '586': 'PK', '795': 'TM', '300': 'GR', '380': 'IT', '470': 'MT', '100': 'BG', '008': 'AL',
  '807': 'MK', '688': 'RS', '070': 'BA', '499': 'ME', '191': 'HR', '642': 'RO', '398': 'KZ', '860': 'UZ',
  '762': 'TJ', '356': 'IN', '204': 'BJ', '768': 'TG', '288': 'GH', '384': 'CI', '430': 'LR', '694': 'SL',
  '250': 'FR', '404': 'KE', '800': 'UG', '180': 'CD', '336': 'VA', '-99': 'XK',
}
// Round them, the neighbours: lon -20..62, lat 3..42.
const inRegion = ([lon, lat]) => lon > -20 && lon < 62 && lat > 3 && lat < 42

const simple = simplify(presimplify(world), quantile(presimplify(world), 0.35))
const out = {}
const unnamed = []
for (const f of feature(simple, simple.objects.countries).features) {
  const rings = (f.geometry?.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry?.coordinates ?? [])
  const all = rings.flat(2)
  if (!all.length) continue
  // The middle of its biggest piece, so France's Guiana does not pull France in.
  const big = rings.reduce((a, b) => (b[0].length > a[0].length ? b : a))[0]
  const mid = [(Math.min(...big.map((p) => p[0])) + Math.max(...big.map((p) => p[0]))) / 2,
    (Math.min(...big.map((p) => p[1])) + Math.max(...big.map((p) => p[1]))) / 2]
  const arab = ARAB[f.id]
  if (!arab && !inRegion(mid)) continue
  // A place Natural Earth draws apart but gives no code (Somaliland, N. Cyprus)
  // is kept by name: only ever background, never a dialect's own.
  const code = arab ?? NEIGHBOURS[f.id] ?? (f.id === undefined ? `x-${f.properties.name}` : null)
  if (!code) { unnamed.push(`${f.id} ${f.properties.name}`); continue }
  const near = arab ? rings : rings.filter((poly) => poly[0].some(inRegion))
  const r = (n) => Math.round(n * 10) / 10
  const pts = []
  const d = near.map((poly) => poly.map((ring) => {
    const xy = ring.map(project).map(([x, y]) => [r(x), r(y)])
    pts.push(...xy)
    const kept = xy.filter((p, i) => i === 0 || p[0] !== xy[i - 1][0] || p[1] !== xy[i - 1][1])
    return 'M' + kept.map((p) => p.join(',')).join('L') + 'Z'
  }).join('')).join('')
  out[code] = {
    name: f.properties.name,
    box: [Math.min(...pts.map((p) => p[0])), Math.min(...pts.map((p) => p[1])), Math.max(...pts.map((p) => p[0])), Math.max(...pts.map((p) => p[1]))],
    d,
  }
}
if (unnamed.length) throw new Error(`No code for: ${unnamed.join('; ')}`)
const file = new URL('../src/data/countryShapes.json', import.meta.url)
writeFileSync(file, JSON.stringify({ _about: 'Natural Earth 1:50m country outlines (public domain), simplified and projected by scripts/countryShapes.mjs. Do not edit by hand.', countries: out }) + '\n')
console.log(Object.keys(out).length, 'countries,', readFileSync(file).length, 'bytes')
