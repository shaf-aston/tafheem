/**
 * Type a surah name and ayah into the Quran tab and the header bar, in a real
 * browser, and confirm the right ayah opens.
 *
 *   node scripts/probe-surahref.mjs
 */
import { chromium } from 'playwright'

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } })
let problems = 0
const check = (label, ok, detail = '') => {
  if (!ok) problems++
  console.log(ok ? 'OK  ' : 'BAD ', label, detail)
}
page.on('pageerror', (e) => { problems++; console.log('PAGEERROR', e.message.slice(0, 300)) })

await page.goto('http://localhost:5173/app?tab=quran', { waitUntil: 'networkidle' })
const box = page.locator('#surah-ref')

await box.fill('Nisa 45')
const rows = page.locator('[aria-label="Matching surahs"] button')
check('suggests An-Nisa for "Nisa 45"', (await rows.first().innerText()).includes('An-Nisa'))
check('row shows the address 4:45', (await rows.first().innerText()).includes('4:45'))
await box.press('Enter')
await page.waitForFunction(() => document.body.innerText.includes('4:45') , null, { timeout: 15000 }).catch(() => {})
await page.waitForTimeout(1500)
check('number fields follow', (await page.locator('#surah-input').inputValue()) === '4' && (await page.locator('#ayah-input').inputValue()) === '45')

await box.fill('Nisa 200')
check('says An-Nisa has 176 ayahs', (await page.locator('body').innerText()).includes('An-Nisa has 176 ayahs'))

await box.fill('kahf')
check('a bare name lists ayah count', (await rows.first().innerText()).includes('110 ayahs'))
await rows.first().click()
await page.waitForTimeout(1500)
check('a bare name opens the surah reader', (await page.locator('body').innerText()).includes('18. Al-Kahf'))

await page.screenshot({ path: process.env.PROBE_SHOT ?? 'probe-surahref.png' })

const bar = page.locator('.cb > .cb-field .cb-input')
await page.goto('http://localhost:5173/app?tab=nahw', { waitUntil: 'networkidle' })
await bar.fill('baqarah 255')
await page.waitForTimeout(400)
check('header bar offers Open ayah 2:255', (await page.locator('body').innerText()).includes('Al-Baqarah 255'))
await bar.press('Enter')
await page.waitForTimeout(1500)
check('bar lands on the Quran tab', new URL(page.url()).searchParams.get('tab') === 'quran')

await browser.close()
console.log(problems ? `${problems} problem(s)` : 'clean')
process.exit(problems ? 1 : 0)
