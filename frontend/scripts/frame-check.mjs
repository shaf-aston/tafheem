/**
 * Frame-time check for motion: does a move keep up with the screen?
 *
 *   node scripts/frame-check.mjs                       (APP=http://localhost:5173)
 *   APP=https://tafheem-app.vercel.app/app CPU=4 node scripts/frame-check.mjs
 *
 * Opens the real app, plays each move below while a requestAnimationFrame loop
 * in the page records the time between frames, and prints, per move, the frames
 * seen, the slowest frame, the 95th percentile, and how many frames ran over
 * twice the screen's frame (a visible stutter). CPU=n throttles the CPU n times
 * (Chrome DevTools), which is how a mid-range phone is approximated on a laptop.
 * Exits 1 when any move drops more than DROP_SHARE of its frames, so it can gate.
 *
 * The screen's frame is taken as the most common gap, so a headless browser
 * (which paints at about 30 frames a second) and a 120 Hz screen are each judged
 * against themselves. Run it headed, or on the deployed app, for real numbers.
 *
 * Each move is a page and something to do there; add one by adding a line.
 */
import { chromium } from 'playwright'

const APP = process.env.APP ?? 'http://localhost:5173'
const CPU = Number(process.env.CPU ?? 1)
const DROP_SHARE = Number(process.env.DROP_SHARE ?? 0.1)
const WATCH_MS = 1200

const MOVES = [
  { name: 'tab change (underline glide, panel arrive)', path: '/quran', act: (p) => p.locator('[role=tab]').nth(2).click() },
  { name: 'More sheet on a phone', path: '/dict', phone: true, act: (p) => p.locator('nav[aria-label=Main] button[aria-label^="All sections"]').click() },
  { name: 'dictionary answer arrives', path: '/dict', act: async (p) => { await p.fill('#dict-input', 'كتب'); await p.press('#dict-input', 'Enter') } },
  { name: 'Grow home worlds reveal', path: '/grow', act: (p) => p.mouse.wheel(0, 1200) },
]

/** Records frame gaps in the page until stopped; returns them in ms. */
const RECORD = () => {
  window.__gaps = []
  let last = performance.now()
  const tick = (now) => {
    window.__gaps.push(now - last)
    last = now
    if (window.__gaps) window.__frame = requestAnimationFrame(tick)
  }
  window.__frame = requestAnimationFrame(tick)
}

const pct = (sorted, p) => sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * p))]

const browser = await chromium.launch(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {})
let failed = false
for (const move of MOVES) {
  const page = await browser.newPage({ viewport: move.phone ? { width: 390, height: 844 } : { width: 1280, height: 800 } })
  if (CPU > 1) await (await page.context().newCDPSession(page)).send('Emulation.setCPUThrottlingRate', { rate: CPU })
  await page.goto(APP + move.path, { waitUntil: 'networkidle' }).catch(() => {})
  await page.waitForTimeout(800)
  await page.evaluate(RECORD)
  try {
    await move.act(page)
  } catch (error) {
    // A move that could not be played is reported, not mistaken for a smooth one.
    console.log(`? ${move.name}: could not play it (${error.message.split('\n')[0]})`)
    failed = true
    await page.close()
    continue
  }
  await page.waitForTimeout(WATCH_MS)
  const gaps = await page.evaluate(() => { cancelAnimationFrame(window.__frame); const g = window.__gaps.slice(1); window.__gaps = null; return g })
  await page.close()
  // The screen's own frame: the most common gap, so a 120 Hz screen is judged at 8 ms.
  const sorted = [...gaps].sort((a, b) => a - b)
  const frame = pct(sorted, 0.5) || 16.7
  const dropped = gaps.filter((gap) => gap > frame * 2).length
  const share = gaps.length ? dropped / gaps.length : 0
  if (share > DROP_SHARE) failed = true
  console.log(`${share > DROP_SHARE ? '✗' : '✓'} ${move.name}: ${gaps.length} frames, p95 ${pct(sorted, 0.95)?.toFixed(1)} ms, worst ${sorted.at(-1)?.toFixed(1)} ms, ${dropped} over ${(frame * 2).toFixed(1)} ms`)
}
await browser.close()
process.exit(failed ? 1 : 0)
