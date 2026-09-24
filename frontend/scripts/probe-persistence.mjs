/**
 * Click-through gate for the remembered choices: set them, reload, read them
 * back. Run against the dev server on 5173 with the backend up.
 */
import { chromium } from 'playwright'

const APP = 'http://localhost:5173'
const problems = []
const check = (name, got, want) => {
  const ok = got === want
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}: ${JSON.stringify(got)}${ok ? '' : ` (wanted ${JSON.stringify(want)})`}`)
  if (!ok) problems.push(name)
}

const pressed = (page, group, label) =>
  page.locator(`[role="group"][aria-label="${group}"] button`, { hasText: label }).getAttribute('aria-pressed')

// Meaning language and direction sit behind one pill labelled with both.
const openSettings = (page) => page.locator('button[aria-expanded]', { hasText: '·' }).first().click()

const browser = await chromium.launch()
const page = await browser.newPage()
page.on('pageerror', (e) => problems.push(`page error: ${e.message}`))

// ── Nahw: which of the two views ─────────────────────────────────────────────
await page.goto(`${APP}/?tab=nahw`)
await page.getByRole('button', { name: /I'raab/ }).click()
await page.waitForSelector('#iraab-input')
await page.reload()
await page.waitForSelector('#iraab-input', { timeout: 5000 }).catch(() => {})
check('nahw view after reload', await pressed(page, 'How close to look at the sentence', "I'raab"), 'true')

// And back, so the remembered value is a choice rather than a one-way door.
await page.getByRole('button', { name: /Tarkeeb/ }).click()
await page.reload()
check('nahw view back to tarkeeb', await pressed(page, 'How close to look at the sentence', 'Tarkeeb'), 'true')

// ── Quiz: the setup, not the round ───────────────────────────────────────────
await page.goto(`${APP}/?tab=quiz`)
await openSettings(page)
await page.getByRole('button', { name: 'EN → AR' }).click()
await page.keyboard.press('Escape')
await page.getByRole('button', { name: 'Everyday' }).click()
await page.getByRole('button', { name: /auto-advance/ }).click()
const autoBefore = await page.getByRole('button', { name: /auto-advance/ }).getAttribute('aria-pressed')

await page.reload()
await openSettings(page)
await page.waitForSelector('[role="group"][aria-label="Direction"]')
check('quiz direction', await pressed(page, 'Direction', 'EN → AR'), 'true')
check('quiz set', await pressed(page, 'Words', 'Everyday'), 'true')
check('quiz auto-advance', await page.getByRole('button', { name: /auto-advance/ }).getAttribute('aria-pressed'), autoBefore)

// A cut inside the Qur'anic set: the kind of cut, then the one inside it.
await page.getByRole('button', { name: "Qur'anic" }).click()
await page.getByRole('button', { name: 'Surah', exact: true }).click()
await page.waitForSelector('select[aria-label="Which surah"]')
await page.selectOption('select[aria-label="Which surah"]', { index: 1 })
const surah = await page.locator('select[aria-label="Which surah"]').inputValue()

await page.reload()
await page.waitForSelector('select[aria-label="Which surah"]', { timeout: 5000 }).catch(() => {})
check('quiz narrow-by', await pressed(page, 'Narrow by', 'Surah'), 'true')
check('quiz surah', await page.locator('select[aria-label="Which surah"]').inputValue(), surah)

// A set with no cuts must ignore a surah remembered under the set that has them.
await page.getByRole('button', { name: 'Everyday' }).click()
await page.reload()
await page.waitForSelector('[role="group"][aria-label="Words"]')
check('no stray cut on a set without cuts', await page.locator('select[aria-label^="Which"]').count(), 0)
const heading = await page.locator('.type-tiny.uppercase').first().textContent()
check('everyday still asks a question', /mean|word/i.test(heading ?? ''), true)

// ── Best streak: the one thing a round leaves behind ─────────────────────────
await page.evaluate(() => localStorage.setItem('quiz-best-streak', '7'))
await page.reload()
await page.waitForSelector('[role="group"][aria-label="Words"]')
check('best streak read back', /best 7/.test(await page.locator('body').innerText()), true)

// ── Recent searches: the row of what has been looked up ──────────────────────
// Seeded with the two scripts mixed and a word asked twice, which is what a real
// history looks like after a week and what the row got wrong: a pill grew to fit
// its own letters, so the Arabic ones stood at twice the height of the English
// ones, and a word asked on two days was kept as two records and drawn twice.
await page.goto(`${APP}/?tab=dict`)
await page.evaluate(() => localStorage.setItem('dict-history', JSON.stringify(
  ['مدرسة', 'spirit', 'food', 'كتب', 'روح', 'food', 'ن-ص-ر']
    .map((q, at) => ({ q, at })))))
await page.reload()
await page.waitForSelector('.recent-row')
const chips = await page.locator('.recent-row button').evaluateAll((all) => ({
  words: all.map((el) => el.innerText.trim()),
  heights: [...new Set(all.map((el) => Math.round(el.getBoundingClientRect().height)))],
  // A long name must widen its pill, never wrap inside a fixed height and
  // spill out of it: the Daleel book chips carry whole Arabic titles.
  spilling: all.filter((el) => el.scrollHeight > el.clientHeight + 1).length,
}))
check('Arabic and English chips are one height', chips.heights.length, 1)
check('the same word twice is one chip', chips.words.filter((w) => w === 'food').length, 1)
check('nothing spills out of a chip', chips.spilling, 0)

// Back to the quiz, which is the tab the clearing below reads its answer from.
await page.goto(`${APP}/?tab=quiz`)
await page.waitForSelector('[role="group"][aria-label="Words"]')

// ── The one button that forgets it all, and does not do it by accident ───────
const stored = () => page.evaluate(() => Object.keys(localStorage).sort())
check('something is being kept', (await stored()).length > 0, true)

await page.getByRole('button', { name: 'Settings', exact: true }).click()
await page.getByRole('button', { name: 'Clear saved data' }).click()
check('one click clears nothing', (await stored()).length > 0, true)

// Armed, it goes quiet again on its own rather than sitting loaded.
await page.waitForTimeout(5400)
check('goes quiet again', await page.getByRole('button', { name: 'Clear saved data' }).count(), 1)

await page.getByRole('button', { name: 'Clear saved data' }).click()
// Wait for the reload itself: the page already counts as loaded before it,
// so waiting on the load state read the old page's storage.
await Promise.all([
  page.waitForNavigation(),
  page.getByRole('button', { name: /Sure\? Clear it all/ }).click(),
])
await page.waitForSelector('[role="group"][aria-label="Words"]')
check('everything forgotten', (await stored()).length, 0)
check('quiz back to its default set', await pressed(page, 'Words', "Qur'anic"), 'true')

await browser.close()
console.log(problems.length ? `\nPROBLEMS: ${problems.join(' | ')}` : '\nCLEAN')
process.exit(problems.length ? 1 : 0)
