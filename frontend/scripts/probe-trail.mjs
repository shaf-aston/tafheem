/**
 * The way back, clicked through: the address bar, the browser's own arrow, and
 * the trail line beside the title. Needs the dev server and the backend up.
 *
 *   node scripts/probe-trail.mjs
 */
import { chromium } from 'playwright'

const APP = 'http://localhost:5173'
const failures = []

const check = (what, got, want) => {
  const ok = String(got) === String(want)
  console.log(`${ok ? 'ok  ' : 'FAIL'}  ${what}${ok ? '' : `  (got ${got}, want ${want})`}`)
  if (!ok) failures.push(what)
}

const search = async (page, word) => {
  await page.fill('#dict-input', word)
  await page.press('#dict-input', 'Enter')
  await page.waitForFunction(
    (w) => new URL(location.href).searchParams.get('q') === w,
    word,
    { timeout: 10000 },
  )
}

// The Dictionary refuses to search while the health check says it has no data,
// so a probe that types before the backend has answered searches nothing.
const ready = (page) => page.getByText('Backend Ready').waitFor({ timeout: 20000 })

const onWord = (page, word) =>
  page.waitForFunction((w) => new URL(location.href).searchParams.get('q') === w, word)

const trail = (page) => page.locator('nav[aria-label="Where you have been"]')

/** Every step in the line, in order, each with where it sits: past, here, ahead. */
const steps = async (page) => {
  const marks = trail(page).locator('[data-step]')
  const out = []
  for (let i = 0; i < await marks.count(); i += 1) {
    const one = marks.nth(i)
    out.push(`${(await one.innerText()).trim()}:${await one.getAttribute('data-step')}`)
  }
  return out.join(' ')
}

const page = await (await chromium.launch()).newPage()
const errors = []
page.on('pageerror', (e) => errors.push(e.message))

await page.goto(`${APP}/?tab=dict`, { waitUntil: 'networkidle' })
await ready(page)
check('nothing walked yet, no trail', await trail(page).count(), 0)

await search(page, 'كتب')
check('the word is in the address', new URL(page.url()).searchParams.get('q'), 'كتب')
check('one step, and it is where we are', await steps(page), 'كتب:here')

await search(page, 'book')
check('two steps, the first now behind', await steps(page), 'كتب:past book:here')

await page.goBack()
await onWord(page, 'كتب')
check('back keeps the one ahead, faded', await steps(page), 'كتب:here book:ahead')
check('and looks the word up again', await page.locator('#dict-input').inputValue(), 'كتب')

await trail(page).locator('[data-step="ahead"]').click()
await onWord(page, 'book')
check('the faded one goes forward', await steps(page), 'كتب:past book:here')

await trail(page).locator('[data-step="past"]').click()
await onWord(page, 'كتب')
check('clicking a step behind goes back to it', await steps(page), 'كتب:here book:ahead')

await trail(page).locator('button[aria-label="Back"]').click()
await page.waitForFunction(() => !new URL(location.href).searchParams.get('q'))
check('the arrow leaves the last word', await steps(page), 'كتب:ahead book:ahead')
check('and there is no arrow left to press', await trail(page).locator('button[aria-label="Back"]').count(), 0)

// A pasted link opens on the word it names, as a new step on the saved path
// (probe-session.mjs covers the path itself). We were on the blank first step,
// so the link is the only word, one step back from nothing.
await page.goto(`${APP}/?tab=dict&q=%D8%B3%D8%B7%D8%B1`, { waitUntil: 'networkidle' })
await ready(page)
check('a shared link opens on that word', await page.locator('#dict-input').inputValue(), 'سطر')
check('as a step on the path', await steps(page), 'سطر:here')

// The line sits on the title's row, so it costs no height of its own.
await search(page, 'كتب')
const rows = await page.evaluate(() => {
  const title = document.querySelector('h2')
  const line = document.querySelector('nav[aria-label="Where you have been"]')
  return [title.getBoundingClientRect(), line.getBoundingClientRect()]
})
// Same row, so it costs no height: the Arabic in it sits lower than a Latin
// baseline, which is why this asks for overlap rather than the same bottom.
check('on the title\'s own row', rows[1].top < rows[0].bottom && rows[1].bottom > rows[0].top, true)
check('and on the right of it', rows[1].left > rows[0].right, true)

// The same line on every tab that looks something up, from one component
// inside SectionHeader. Each tab keeps its own path.
for (const [tab, field, first, second] of [
  ['daleel', '#daleel-input', 'patience', 'الصبر'],
  ['sarf', '#sarf-input', 'كتب', 'درس'],
]) {
  await page.goto(`${APP}/?tab=${tab}`, { waitUntil: 'networkidle' })
  await ready(page)
  for (const word of [first, second]) {
    await page.fill(field, word)
    await page.press(field, 'Enter')
    await page.waitForFunction(
      (w) => new URL(location.href).searchParams.get('q') === w, word, { timeout: 20000 },
    )
  }
  check(`${tab} has the same line`, await steps(page), `${first}:past ${second}:here`)
  await page.goBack()
  await onWord(page, first)
  check(`${tab} goes back the same way`, await steps(page), `${first}:here ${second}:ahead`)
}

check('no page errors', errors.join(' | '), '')
console.log(failures.length ? `\n${failures.length} FAILED` : '\nCLEAN')
process.exit(failures.length ? 1 : 0)
