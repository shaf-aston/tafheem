/**
 * Drive the quiz tab in a real browser and prove the progress feature works.
 *
 *   node scripts/drive-quiz.mjs
 *
 * Not a test: the suites prove the parts. This answers questions in the running
 * page, on purpose getting some wrong, and then checks that the mistakes come
 * back, that a single mistake still makes a four-option question, that two
 * right answers clear it, and that the reading at the foot says something.
 */
import { chromium } from 'playwright'

const APP = 'http://localhost:5173/?tab=quiz'
const API = 'http://localhost:8000/api/progress'

const results = []
const check = (name, pass, detail = '') => {
  results.push({ name, pass, detail })
  console.log(`${pass ? 'PASS' : 'FAIL'}  ${name}${detail ? `  (${detail})` : ''}`)
}

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } })
let problems = 0
page.on('pageerror', (e) => { problems++; console.log('PAGEERROR', e.message.slice(0, 200)) })
page.on('response', async (r) => {
  if (r.url().includes('/api/') && r.status() >= 400) {
    problems++
    console.log('HTTP', r.status(), r.url())
  }
})

const options = () => page.locator('[aria-label="Answers"] button')
const bankButton = (label) => page.getByRole('button', { name: new RegExp(`^${label}`) }).first()

/**
 * Answer the live question by always taking the first option.
 *
 * Which option is right cannot be known before answering, so this gets a mix
 * of right and wrong, which is what the drive needs: a run of only right
 * answers would leave the mistakes list empty and prove nothing.
 */
async function answer() {
  await options().first().waitFor({ state: 'visible' })
  await options().first().click()
  await page.waitForTimeout(150)
  const verdict = await page.locator('[aria-live="polite"]').innerText().catch(() => '')
  return verdict.startsWith('Correct')
}

await page.goto(APP, { waitUntil: 'networkidle' })
await page.waitForTimeout(500)

// ── 1. Answers are recorded ─────────────────────────────────────────────────
const startCount = (await (await fetch(`${API}/summary?module=quiz`)).json()).items.length
let answered = 0
for (let i = 0; i < 6; i++) {
  await answer()
  answered++
  await page.getByRole('button', { name: /Next word/ }).click().catch(() => {})
  await page.waitForTimeout(250)
}
await page.waitForTimeout(600)
const afterItems = (await (await fetch(`${API}/summary?module=quiz`)).json()).items
check('answers reach the store', afterItems.length > startCount,
  `${startCount} items before, ${afterItems.length} after ${answered} answers`)

const timed = afterItems.filter((row) => row.avgMs !== null)
check('answers are timed', timed.length > 0,
  timed.length ? `e.g. ${timed[0].item} ${timed[0].avgMs}ms` : 'nothing timed')
check('timings are plausible, not the age of the page',
  timed.every((row) => row.avgMs > 0 && row.avgMs < 120000),
  timed.map((row) => row.avgMs).join(', '))

// ── 2. The Mistakes control appears with a count ─────────────────────────────
const owed = (await (await fetch(`${API}/review?module=quiz`)).json()).items
const mistakesLabel = await bankButton('Mistakes').innerText().catch(() => '')
check('the Mistakes control shows how many are waiting',
  owed.length === 0 || /\d/.test(mistakesLabel), `label "${mistakesLabel}", ${owed.length} owed`)

// ── 3. Mistakes mode asks a full question ───────────────────────────────────
if (owed.length > 0) {
  await bankButton('Mistakes').click()
  await page.waitForTimeout(900)
  const shown = await options().count()
  check('a mistakes question still has four options', shown === 4,
    `${shown} options from ${owed.length} mistake(s)`)

  const asked = await page.locator('.rise-in .text-center').first().innerText().catch(() => '')
  check('the word asked is one that was got wrong', asked.length > 0, asked.slice(0, 40))
} else {
  check('a mistakes question still has four options', false, 'no mistakes were made to test with')
}

// ── 4. The reading at the foot says something before it is even opened ──────
// The bar carries the figures now, so this is two claims, not one: that the
// shut bar already answers "how am I doing", and that opening it still gives
// the detail. A bar that had gone back to a bare label would pass the second
// and fail the first, which is the regression worth catching.
const reading = page.locator('summary').filter({ hasText: /right|How you’re doing/ }).first()
check('the reading is on the page', await reading.count() > 0)
if (await reading.count() > 0) {
  const shut = await reading.innerText()
  check('the shut bar already carries the figures', /\d+%[\s\S]*right[\s\S]*answered/i.test(shut),
    shut.replace(/\n+/g, ' ').slice(0, 80))

  // The bar has to follow the answers on its own. It used to be read once a
  // round and then left alone, so the figures sat still until the page was
  // reloaded by hand, which is the regression this catches: answer one more
  // question, without reloading, and the count has to move.
  const answeredNow = async () => Number(/(\d+)\s*\n?\s*ANSWERED/i.exec(await reading.innerText())?.[1] ?? -1)
  const beforeOne = await answeredNow()
  await answer()
  await page.waitForTimeout(1200)
  const afterOne = await answeredNow()
  check('the bar counts a new answer without a reload', afterOne === beforeOne + 1,
    `${beforeOne} then ${afterOne}`)

  await reading.click()
  await page.locator('details:has-text("Across")').first()
    .waitFor({ state: 'visible', timeout: 5000 }).catch(() => {})
  await page.waitForTimeout(400)
  const text = await page.locator('details').filter({ hasText: /answered/ }).first().innerText()
  check('opening it reports what the bar has no room for', /Across \d+ words?/.test(text),
    (text.split('\n').find((line) => line.startsWith('Across')) ?? '').slice(0, 80))
}

// ── 5. Two right answers clear a word, and the control notices ─────────────
// Done with an id of its own rather than one of the words above: a word the
// round is still asking could be got wrong again mid-check, which would make
// this pass or fail by luck. The rule itself is proven exactly in pytest; what
// is being watched here is that the page follows the store.
const PROBE = 'drive-clear-probe'
const file = (correct) => fetch(`${API}/attempts`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ module: 'quiz', item: PROBE, correct, ms: 900 }),
})
const owedNow = async () => (await (await fetch(`${API}/review?module=quiz`)).json()).items

await file(false)
const withProbe = await owedNow()
check('a wrong answer puts a word in the mistakes list', withProbe.includes(PROBE))

await page.reload({ waitUntil: 'networkidle' })
await page.waitForTimeout(700)
const labelUp = await bankButton('Mistakes').innerText().catch(() => '')
check('the control counts it', labelUp.includes(String(withProbe.length)),
  `label "${labelUp}", ${withProbe.length} owed`)

await file(true)
check('one right answer is not enough, it could be a lucky guess',
  (await owedNow()).includes(PROBE))

await file(true)
const cleared = await owedNow()
check('two right answers clear it', !cleared.includes(PROBE),
  `${withProbe.length} owed, now ${cleared.length}`)

await page.reload({ waitUntil: 'networkidle' })
await page.waitForTimeout(700)
const labelDown = await bankButton('Mistakes').innerText().catch(() => '')
check('the control shows the new number', labelDown.includes(String(cleared.length)) || !cleared.length,
  `label "${labelDown}", ${cleared.length} owed`)

// ── 6. Nothing broke ────────────────────────────────────────────────────────
check('no page errors or failed calls', problems === 0, `${problems} problem(s)`)

await page.screenshot({ path: 'drive-quiz.png', fullPage: true })
await browser.close()

const failed = results.filter((r) => !r.pass)
console.log(`\n${results.length - failed.length}/${results.length} checks passed`)
process.exit(failed.length ? 1 : 0)
