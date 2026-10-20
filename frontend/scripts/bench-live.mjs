/**
 * Real speed numbers for the live site: time until each page shows its content.
 *
 *   npm run bench:live                     # Oracle, fast line
 *   npm run bench:live -- <base> phone     # same, throttled like a phone on 4G
 *
 * first  = new visitor, nothing saved.  again = same visitor opens it a second time.
 * Each is the median of RUNS tries, plus the bytes the browser had to download.
 */
import { chromium } from 'playwright'

const BASE = (process.argv[2] ?? 'https://tafheem-app.vercel.app').replace(/\/$/, '')
const PHONE = process.argv[3] === 'phone'
const RUNS = Number(process.env.RUNS ?? 5)

const PAGES = [
  ['landing', '/', /Tafheem/i],
  ['nahw', '/app?tab=nahw&view=analyse&q=ذهب الطالب', /jumlah/i],
  ['dictionary', '/app?tab=dict&q=كتب', /\d+ entries/],
  ['quiz', '/app?tab=quiz', /What does this mean/i],
]

const median = (xs) => xs.sort((a, b) => a - b)[xs.length >> 1]

async function visit(context, path, text) {
  const page = await context.newPage()
  if (PHONE) {
    const cdp = await context.newCDPSession(page)
    // Chrome DevTools "Fast 4G": 150 ms latency, 9 Mbit down, 4x slower processor
    await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 150, downloadThroughput: 9e6 / 8, uploadThroughput: 1.5e6 / 8 })
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 })
  }
  const t0 = Date.now()
  await page.goto(BASE + encodeURI(path))
  await page.getByText(text).first().waitFor({ timeout: 60000 })
  const ms = Date.now() - t0
  // bytes really sent over the wire; files kept by the browser count 0
  const bytes = await page.evaluate(() => performance.getEntries().reduce((n, e) => n + (e.transferSize ?? 0), 0))
  await page.close()
  return { ms, kb: bytes / 1024 }
}

const browser = await chromium.launch()
console.log(`${BASE} ${PHONE ? 'phone 4G' : 'fast line'}, median of ${RUNS}`)
console.log('page         first ms   again ms   first KB  again KB')
for (const [name, path, text] of PAGES) {
  const first = [], again = []
  for (let i = 0; i < RUNS; i++) {
    const context = await browser.newContext()
    first.push(await visit(context, path, text))
    again.push(await visit(context, path, text))
    await context.close()
  }
  const f = median(first.map((x) => x.ms)), a = median(again.map((x) => x.ms))
  const fk = median(first.map((x) => x.kb)), ak = median(again.map((x) => x.kb))
  console.log(`${name.padEnd(12)} ${String(f).padStart(8)} ${String(a).padStart(10)} ${String(Math.round(fk)).padStart(10)} ${String(Math.round(ak)).padStart(9)}`)
}
await browser.close()
