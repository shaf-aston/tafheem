/**
 * Headless pass/fail check of every tab on a running site, no screenshots to read.
 *
 *   npm run check:live                               # Oracle
 *   npm run check:live -- https://tafheem-app.vercel.app
 *   npm run check:live -- http://localhost:5173
 *
 * Each page must: load, make its backend call with a 2xx answer, show the
 * expected text, and throw no page error. Prints one line per page with the
 * seconds it took; exits non-zero on any failure.
 */
import { chromium } from 'playwright'

const BASE = (process.argv[2] ?? 'https://tafheem-app.vercel.app').replace(/\/$/, '')
const TIMEOUT = 20000

// [name, path, backend call it must make, text the page must then show]
const PAGES = [
  ['landing', '/', null, /Tafheem/i],
  ['nahw analyse', '/app?tab=nahw&view=analyse&q=ذهب الطالب', '/api/analyze', /jumlah/i],
  ['dictionary', '/app?tab=dict&q=كتب', '/api/dictionary/search', /\d+ entries/],
  ['quran', '/app?tab=quran', '/api/health', /Surah, ayah or Arabic text/i],
  ['daleel', '/app?tab=daleel&q=رحمة', '/api/daleel', /رحم/],
  ['sarf', '/app?tab=sarf', '/api/health', /Bāb Nasara/],
  ['memorise', '/app?tab=mem', '/api/health', /Fill in the gaps/],
  ['quiz', '/app?tab=quiz', '/api/health', /What does this mean/i],
  ['timelines', '/app?tab=timelines', '/api/timelines', /Signs of the Hour/],
  ['hadith', '/app?tab=hadith', '/api/hadith/collections', /Sahih al-Bukhari/],
  ['grow', '/app?tab=grow', '/api/grow/paths', /mastered/],
  ['colloquial', '/app?tab=colloq', '/api/colloquial/damascene/unit-01', /First Conversations/],
]

const browser = await chromium.launch()
let fails = 0
for (const [name, path, call, text] of PAGES) {
  const page = await browser.newPage()
  const errors = []
  page.on('pageerror', (e) => errors.push('page error: ' + e.message.slice(0, 120)))
  page.on('response', (r) => {
    if (r.url().includes('/api/') && r.status() >= 400) errors.push(`${r.status()} ${new URL(r.url()).pathname}`)
  })
  const t0 = Date.now()
  try {
    const waitCall = call && page.waitForResponse((r) => new URL(r.url()).pathname === call && r.ok(), { timeout: TIMEOUT })
    await page.goto(BASE + encodeURI(path), { timeout: TIMEOUT })
    if (waitCall) await waitCall
    await page.getByText(text).first().waitFor({ timeout: TIMEOUT })
    // A tab can render its heading and still say its data is missing on the server.
    if (await page.getByText(/not installed|No collection is built yet|Could not load/i).count()) errors.push('page says its data is missing')
    // A tab can render its heading and still say its data is missing on the server.
    const missing = await page.getByText(/not installed|No collection is built yet|Could not load/i).count()
    if (missing) errors.push('page says its data is missing')
  } catch (e) {
    errors.push(e.message.split('\n')[0].slice(0, 120))
  }
  const s = ((Date.now() - t0) / 1000).toFixed(1)
  console.log(`${errors.length ? 'FAIL' : 'ok  '} ${name.padEnd(14)} ${s}s ${errors.join('; ')}`)
  if (errors.length) fails++
  await page.close()
}
await browser.close()
console.log(`${BASE}: ${PAGES.length - fails}/${PAGES.length} pages ok`)
process.exit(fails ? 1 : 0)
