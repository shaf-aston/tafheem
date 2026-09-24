/**
 * Does the walked path survive a reload? Clicked through, not assumed. Needs
 * the dev server and the backend up.
 *
 *   node scripts/probe-session.mjs
 */
import { chromium } from 'playwright'

const APP = 'http://localhost:5173'
const failures = []

const check = (what, got, want) => {
  const ok = String(got) === String(want)
  console.log(`${ok ? 'ok  ' : 'FAIL'}  ${what}${ok ? '' : `  (got ${got}, want ${want})`}`)
  if (!ok) failures.push(what)
}

const ready = (page) => page.getByText('Backend Ready').waitFor({ timeout: 20000 })

const onWord = (page, word) =>
  page.waitForFunction((w) => new URL(location.href).searchParams.get('q') === w, word, { timeout: 15000 })

const search = async (page, field, word) => {
  await page.fill(field, word)
  await page.press(field, 'Enter')
  await onWord(page, word)
}

const trail = (page) => page.locator('nav[aria-label="Where you have been"]')

const steps = async (page) => {
  const marks = trail(page).locator('[data-step]')
  const out = []
  for (let i = 0; i < await marks.count(); i += 1) {
    const one = marks.nth(i)
    out.push(`${(await one.innerText()).trim()}:${await one.getAttribute('data-step')}`)
  }
  return out.join(' ')
}

const saved = (page) => page.evaluate(() => JSON.parse(localStorage.getItem('session') || 'null'))

const page = await (await chromium.launch()).newPage()
const errors = []
page.on('pageerror', (e) => errors.push(e.message))

await page.goto(`${APP}/?tab=dict`, { waitUntil: 'networkidle' })
await ready(page)
await search(page, '#dict-input', 'كتب')
await search(page, '#dict-input', 'book')
check('walked two words', await steps(page), 'كتب:past book:here')
check('and the path is on disk', (await saved(page))?.steps?.length, 3)

// 1. A plain reload.
await page.reload({ waitUntil: 'networkidle' })
await ready(page)
check('reload keeps the path', await steps(page), 'كتب:past book:here')
check('reload keeps the word on screen', await page.locator('#dict-input').inputValue(), 'book')
check('reload keeps the back arrow', await trail(page).locator('button[aria-label="Back"]').count(), 1)

// 2. The browser's own arrow, after a reload. The browser reloads the page for
//    that entry and hands back the step it stored, so we land on the saved step.
await page.goBack({ waitUntil: 'networkidle' })
await ready(page)
await onWord(page, 'كتب')
check('back after a reload lands on the step before', await steps(page), 'كتب:here book:ahead')
check('and shows that word', await page.locator('#dict-input').inputValue(), 'كتب')

// 3. Reload while sitting on an earlier step: the step ahead is still ahead.
await page.reload({ waitUntil: 'networkidle' })
await ready(page)
check('reload on an earlier step keeps what is ahead', await steps(page), 'كتب:here book:ahead')

// 4. A pasted link is a new place after the current one; what was ahead goes.
await page.goto(`${APP}/?tab=dict&q=%D8%B3%D8%B7%D8%B1`, { waitUntil: 'networkidle' })
await ready(page)
check('a pasted link joins the path', await steps(page), 'كتب:past سطر:here')

// 5. Another tab, then back to this one from the strip with nothing in hand:
//    it opens on the word it was on.
await page.locator('#tab-daleel').click()
await page.waitForFunction(() => new URL(location.href).searchParams.get('tab') === 'daleel')
check('daleel opens blank, it has no last word', new URL(page.url()).searchParams.get('q'), null)
await page.locator('#tab-dict').click()
await onWord(page, 'سطر')
check('the dictionary reopens on its last word', await page.locator('#dict-input').inputValue(), 'سطر')
check('and the return is drawn once, not twice', await steps(page), 'كتب:past سطر:here')

// 5b. A bare address, the way a bookmark opens: the tab's last word, not a blank.
await page.goto(`${APP}/?tab=dict`, { waitUntil: 'networkidle' })
await ready(page)
check('a bare address opens on the last word', await page.locator('#dict-input').inputValue(), 'سطر')
check('and the address now says so', new URL(page.url()).searchParams.get('q'), 'سطر')

// 5c. The app's own address, no tab at all: where the reader last was.
await page.goto(`${APP}/`, { waitUntil: 'networkidle' })
await ready(page)
check('the root address opens on the last tab', new URL(page.url()).searchParams.get('tab'), 'dict')
check('and its last word', await page.locator('#dict-input').inputValue(), 'سطر')

// 6. A path older than its shelf life is not yours any more.
await page.evaluate(() => {
  const record = JSON.parse(localStorage.getItem('session'))
  record.saved -= 13 * 60 * 60 * 1000
  localStorage.setItem('session', JSON.stringify(record))
})
await page.reload({ waitUntil: 'networkidle' })
await ready(page)
// One step with nothing behind it is no trail at all; the word itself still
// comes from the address, as any first open does.
check('a stale path opens clean, no trail', await trail(page).count(), 0)
check('the address still says the word', await page.locator('#dict-input').inputValue(), 'سطر')
check('and the path is written fresh', (await saved(page))?.steps?.length, 1)

// 6b. The browser still holds entries from before the path expired. Pressing
//     back into one must follow the address, not leave the panel behind it.
await search(page, '#dict-input', 'كتب')
check('a new word after the stale start', await steps(page), 'سطر:past كتب:here')
await page.evaluate(() => {
  const record = JSON.parse(localStorage.getItem('session'))
  record.saved -= 13 * 60 * 60 * 1000
  localStorage.setItem('session', JSON.stringify(record))
})
await page.reload({ waitUntil: 'networkidle' })
await ready(page)
check('expired again, one word, no trail', await trail(page).count(), 0)
await page.goBack({ waitUntil: 'networkidle' })
await ready(page)
await onWord(page, 'سطر')
check('back into old history still shows that word', await page.locator('#dict-input').inputValue(), 'سطر')
check('and it is walked onto the path', await steps(page), 'كتب:past سطر:here')

// 7. A hand-edited or broken record is dropped, never crashes the page.
for (const junk of ['{"v":1,"saved":1,"steps":"x","at":0}', 'not json', '{"v":1,"saved":' + Date.now() + ',"steps":[{"tab":"iraab","value":"a"}],"at":9}']) {
  await page.evaluate((raw) => localStorage.setItem('session', raw), junk)
  await page.reload({ waitUntil: 'networkidle' })
  await ready(page)
  check(`junk record opens clean: ${junk.slice(0, 18)}`, await trail(page).count(), 0)
  check('and is replaced by a good one', (await saved(page))?.steps?.length, 1)
}

check('no page errors', errors.join(' | '), '')
console.log(failures.length ? `\n${failures.length} FAILED` : '\nCLEAN')
process.exit(failures.length ? 1 : 0)
