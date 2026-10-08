/**
 * Does the Qur'an face keep its marks close to its letters? Draws every distinct
 * word of the 114 surahs in the face the reader uses and measures how tall its
 * ink stands (marks above plus marks below). A line is --arabic-line-height tall;
 * where a word's ink is taller than that, its marks run into the neighbouring
 * line. Run it before changing --font-quran or the line height.
 *
 *   node scripts/probe-quran-script.mjs        (dev server and backend running)
 *
 * Measured 2026-10: Amiri Quran p99 2.46em (tangled lines), Scheherazade New 1.87em.
 * Coverage is the other half of the check: every character the text uses must be
 * in the face, or the browser draws it from a fallback with marks in other places.
 * The text uses 73 characters; fontTools' getBestCmap() on the woff lists the gaps.
 */
import { chromium } from 'playwright'

const BASE = process.env.BASE ?? 'http://localhost:5173'
const SURAHS = 114
const PERCENTILE = 0.99 // the rare tallest words may touch; the usual ones must not
const MEASURE_PX = 100 // big enough that canvas measures whole pixels of ink

const browser = await chromium.launch()
const page = await browser.newPage()
await page.goto(`${BASE}/app?tab=quran`, { waitUntil: 'networkidle' })

const { family, lineHeight, heights } = await page.evaluate(async ({ SURAHS, MEASURE_PX }) => {
  const root = getComputedStyle(document.documentElement)
  const family = root.getPropertyValue('--font-quran').trim()
  const lineHeight = parseFloat(root.getPropertyValue('--arabic-line-height'))
  const words = new Set()
  for (let s = 1; s <= SURAHS; s++) {
    const { ayahs } = await (await fetch(`/api/quran/surah/${s}`)).json()
    for (const a of ayahs) for (const w of a.arabic.split(' ')) words.add(w)
  }
  await document.fonts.load(`${MEASURE_PX}px ${family}`, 'بِسْمِ')
  const ctx = document.createElement('canvas').getContext('2d')
  ctx.font = `${MEASURE_PX}px ${family}`
  ctx.direction = 'rtl'
  const heights = [...words].map((w) => {
    const m = ctx.measureText(w)
    return (m.actualBoundingBoxAscent + m.actualBoundingBoxDescent) / MEASURE_PX
  })
  return { family, lineHeight, heights: heights.sort((a, b) => a - b) }
}, { SURAHS, MEASURE_PX })
await browser.close()

const tall = heights[Math.floor(PERCENTILE * heights.length)]
const ok = tall <= lineHeight
console.log(`${ok ? 'OK  ' : 'BAD '} ${family}: ${heights.length} words, p${PERCENTILE * 100} ink ${tall.toFixed(2)}em, line ${lineHeight}em, tallest ${heights.at(-1).toFixed(2)}em`)
process.exit(ok ? 0 : 1)
