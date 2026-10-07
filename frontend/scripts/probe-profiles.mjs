/**
 * Prove a typed name is one record across devices.
 *
 *   node scripts/probe-profiles.mjs
 *
 * Needs the app on :5173 and the backend on :8000. Two browser contexts stand
 * in for a phone and a laptop: they share nothing but the server. A types a
 * name, answers two quiz questions and reloads; B types the same name. Both
 * must read the same count, and a third name must read none of it.
 */
import { chromium } from 'playwright'

const APP = 'http://localhost:5173/app?tab=quiz'
const NAME = `probe-${Date.now()}`

let failed = 0
const check = (name, pass, detail = '') => {
  if (!pass) failed++
  console.log(`${pass ? 'PASS' : 'FAIL'}  ${name}${detail ? `  (${detail})` : ''}`)
}

// PW_CHROMIUM: a browser already on disk, when the pinned one is not installed.
const browser = await chromium.launch({ executablePath: process.env.PW_CHROMIUM })

async function device(label) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 1000 } })
  const page = await context.newPage()
  page.on('pageerror', (e) => console.log(label, 'PAGEERROR', e.message.slice(0, 200)))
  page.on('response', (r) => {
    if (r.url().includes('/api/progress') && r.status() >= 400) console.log(label, 'HTTP', r.status(), r.url())
  })
  await page.goto(APP, { waitUntil: 'networkidle' })
  return page
}

async function typeName(page, name, keep = false) {
  await page.locator('button[title="Switch name"], button:has-text("Who\'s learning?")').first().click()
  await page.locator('#profile-name').fill(name)
  const box = page.getByLabel('Keep progress from this device')
  if (await box.count()) await box.setChecked(keep)
  await page.getByRole('button', { name: /^(Save|Switch)$/ }).click()
  await page.waitForTimeout(400)
}

/** Answers on the server for `name`, read the way the page reads them. */
const attempts = (page, name) => page.evaluate(async (who) => {
  const response = await fetch('/api/progress/summary?module=quiz', {
    headers: who ? { 'X-Tafheem-Profile': encodeURIComponent(who) } : {},
  })
  const { items } = await response.json()
  return items.reduce((sum, row) => sum + row.attempts, 0)
}, name)

// Device A: name, two answers, reload.
const a = await device('A')
await typeName(a, NAME)
for (let i = 0; i < 2; i++) {
  const options = a.locator('[aria-label="Answers"] button')
  await options.first().waitFor({ state: 'visible' })
  await options.first().click()
  await a.waitForTimeout(300)
  await a.getByRole('button', { name: /Next word/ }).click().catch(() => {})
  await a.waitForTimeout(300)
}
await a.waitForTimeout(600)
await a.reload({ waitUntil: 'networkidle' })
const shown = await a.getByRole('button', { name: NAME }).count()
check('the name survives a reload', shown > 0)
const onA = await attempts(a, NAME)
check('two answers filed under the name', onA === 2, `${onA}`)

// Device B: same name typed by hand, different letter case and spaces.
const b = await device('B')
await typeName(b, `  ${NAME.toUpperCase()} `)
const onB = await attempts(b, NAME)
check('the same name on another device reads the same record', onB === onA, `A ${onA}, B ${onB}`)

// A different name reads nothing of it.
const other = await attempts(b, `${NAME}-other`)
check('another name reads none of it', other === 0, `${other}`)

// Switching name on A refetches progress under the new name, not the old one.
const asked = []
a.on('request', (r) => {
  if (r.url().includes('/api/progress/review')) asked.push(decodeURIComponent(r.headers()['x-tafheem-profile'] ?? ''))
})
await typeName(a, `${NAME}-b`)
await a.waitForTimeout(800)
check('switching name refetches under the new name', asked.includes(`${NAME}-b`), asked.join(', ') || 'no refetch')

// Clean up the probe's record.
await a.evaluate((who) => fetch('/api/progress', {
  method: 'DELETE', headers: { 'X-Tafheem-Profile': encodeURIComponent(who) },
}), NAME)

await browser.close()
console.log(failed ? `${failed} FAILED` : 'ALL PASS')
process.exit(failed ? 1 : 0)
