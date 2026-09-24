/**
 * Memorise > Recite it, clicked through rather than assumed. Needs the dev
 * server and the backend up.
 *
 *   node scripts/probe-recite.mjs
 *
 * Two things it proves, both of which only exist on the running page: pressing
 * a word starts the recitation there, so the words above it stay printed and
 * the count of covered words drops by exactly that many; and asking for help
 * uncovers one word, or the rest of the ayah, and marks it as given.
 */
import { chromium } from 'playwright'

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } })
page.on('pageerror', (e) => console.log('PAGEERROR', e.message.slice(0, 300)))
page.on('console', (m) => { if (m.type() === 'error') console.log('CONSOLE', m.text().slice(0, 200)) })

await page.goto('http://localhost:5173/?tab=mem', { waitUntil: 'networkidle' })
await page.getByRole('button', { name: 'Recite it' }).click()
await page.waitForTimeout(600)

console.log('hint:', await page.getByText('tap a word to start').isVisible())

const covers = () => page.locator('[aria-label="a word to say from memory"]').count()
const starts = () => page.locator('button[aria-label^="start reciting from"]').count()
console.log('start buttons:', await starts(), 'covered:', await covers())

// Start from the third word on the page.
await page.locator('button[aria-label^="start reciting from"]').nth(2).click()
await page.waitForTimeout(400)
console.log('after tapping the 3rd word, covered:', await covers())

const shownCount = () => page.locator('span[title="shown, not remembered"]').count()
await page.getByRole('button', { name: 'Show a word' }).click()
await page.waitForTimeout(200)
console.log('after Show a word:', 'shown', await shownCount(), 'covered', await covers())
await page.getByRole('button', { name: 'Show a word' }).click()
await page.waitForTimeout(200)
console.log('twice:', 'shown', await shownCount(), 'covered', await covers())
await page.getByRole('button', { name: 'Show this ayah' }).click()
await page.waitForTimeout(200)
console.log('after Show this ayah:', 'shown', await shownCount(), 'covered', await covers())

console.log('new gaps gone while reciting:', await page.getByRole('button', { name: 'New gaps' }).count())
await page.screenshot({ path: process.env.SHOT ?? 'recite.png', fullPage: true })
await browser.close()
