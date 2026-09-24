/**
 * Does the page work out where somebody started reciting, without being told?
 *
 *   node scripts/probe-start.mjs
 *
 * The suites prove follow.js answers `began` for lists of strings. This proves
 * the running page acts on it: the microphone is a real one Chrome fakes, and
 * the engine's answer is intercepted and replaced with a recitation that begins
 * at the fifth ayah of al-Fatihah, which nobody told the page about.
 *
 * What must happen: the page opens with only its first word showing, follows
 * from 1:5 once it has heard enough, leaves 1:1 to 1:4 printed rather than
 * accusing them of being skipped, and still lets a press of a word overrule it.
 */
import { chromium } from 'playwright'

// 1:5 to 1:7, spelled the plain way a microphone writes it, not as printed.
const HEARD = 'إياك نعبد وإياك نستعين اهدنا الصراط المستقيم'

const results = []
const check = (name, pass, detail = '') => {
  results.push(pass)
  console.log(`${pass ? 'PASS' : 'FAIL'}  ${name}${detail ? `  (${detail})` : ''}`)
}

const browser = await chromium.launch({
  args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'],
})
const page = await browser.newPage({
  viewport: { width: 1280, height: 1000 },
  permissions: ['microphone'],
})
page.on('pageerror', (e) => console.log('PAGEERROR', e.message.slice(0, 200)))

// The engine, answered here instead of over the network: this probe is about
// what the page does with a reading, not about whether Groq heard it.
let asked = 0
await page.route('**/api/listen*', async (route) => {
  asked += 1
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ text: HEARD, ayahs: [] }),
  })
})

await page.goto('http://localhost:5173/?tab=mem', { waitUntil: 'networkidle' })
await page.getByRole('button', { name: 'Recite it' }).click()
await page.waitForTimeout(500)

const covered = () => page.locator('[aria-label="a word to say from memory"]').count()
const words = await page.locator('button[aria-label^="start reciting from"]').count()
check('the page opens with one word showing', (await covered()) === words - 1, `${await covered()} of ${words}`)

// The strip's own button, by its exact name: every word on the page is also a
// button whose label starts "start reciting from".
await page.getByRole('button', { name: 'Start reciting', exact: true }).click()
// One window of sound is four seconds, so anything shorter asks nothing.
await page.waitForTimeout(6000)

// Read while it is still listening: this is the thing the reciter sees.
const hint = page.getByText(/following you from|listening for where you are|tap a word to start/)
const line = await hint.first().innerText().catch(() => '')
check('the engine was asked', asked > 0, `${asked} readings`)
check('it says which ayah it is following from', /following you from\s*5/.test(line), line.trim())

await page.getByRole('button', { name: 'Stop', exact: true }).click()
await page.waitForTimeout(2000)
check('it still says so after stopping', /following you from\s*5/.test(await hint.first().innerText()))

// 1:1 to 1:4 is 15 words in the Madani layout; none of them may be accused of
// having been skipped, because nobody claimed to have recited them.
const missed = await page.locator('span[style*="--danger"]').count()
check('the words above the start are not called skipped', missed === 0, `${missed} accused`)

// And the reader still wins: pressing the first word pins the start back to it.
await page.locator('button[aria-label^="start reciting from"]').first().click()
await page.waitForTimeout(400)
const after = await hint.first().innerText().catch(() => '')
check('pressing a word overrules it', /following you from\s*1|tap a word/.test(after), after.trim())

await page.screenshot({ path: process.env.SHOT ?? 'probe-start.png', fullPage: true })
await browser.close()
console.log(results.every(Boolean) ? '\nall passed' : '\nsomething failed')
process.exit(results.every(Boolean) ? 0 : 1)
