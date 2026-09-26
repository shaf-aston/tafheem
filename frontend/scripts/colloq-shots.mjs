/**
 * Colloquial tab at the four widths the plan names: the unit list and one full
 * lesson, screenshotted, with an axe check on each.
 *
 *   npm run dev   (in another shell)
 *   node scripts/colloq-shots.mjs [outDir]
 *
 * Uses the real first unit when there is one. With the folder empty it puts a
 * placeholder unit there for the run and deletes it after: English letters
 * only, so no Arabic is authored, and it proves layout, not content.
 */
import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { chromium } from 'playwright'

const WIDTHS = [390, 768, 1280, 1600]
const DATA = new URL('../src/data/colloquial/', import.meta.url)
const config = JSON.parse(readFileSync(new URL('../src/colloquial.json', import.meta.url)))
const out = process.argv[2] ?? 'shots/colloq'
mkdirSync(out, { recursive: true })

const placeholder = new URL('unit-00.json', DATA)
rmSync(placeholder, { force: true }) // left by a run that was cut short
const empty = !readdirSync(DATA).some((f) => f.endsWith('.json'))
if (empty) {
  const MIN = config['lesson-minimums']
  const many = (n, make) => Array.from({ length: n }, (_, i) => make(i + 1))
  const line = (i) => ({ ar: `placeholder line ${i}`, translit: `translit ${i}`, en: `English ${i}` })
  writeFileSync(placeholder, JSON.stringify({
    unit: 'unit-00', title: 'Placeholder unit',
    lessons: [{
      id: '0.1', situation: 'Placeholder situation', goal: 'Placeholder goal',
      phrases: many(MIN.phrases, (i) => ({ ...line(i), use: `use ${i}`, reply: i % 2 ? line(i) : null })),
      dialogue: many(MIN.dialogue, (i) => ({ speaker: i % 2 ? 'A' : 'B', ...line(i) })),
      de_book: many(MIN.de_book, (i) => ({ book: `book ${i}`, natural: `natural ${i}`, why: `why ${i}` })),
      grammar: null, culture: 'Placeholder culture note',
      exercises: many(MIN.exercises, (i) => ({ id: `0.1-e${i}`, type: 'say_it', prompt: 'p', answer: 'a', accepted: ['a'], too_formal: [], tip: 't' })),
    }],
    challenge: { scenario: '', partner_role: '', learner_goals: [], target_phrases: [], checklist: [] },
  }))
}

const axe = readFileSync(new URL('../node_modules/axe-core/axe.min.js', import.meta.url), 'utf8')
// The app's own tab strip is left out: its finding predates this tab and is not in its scope.
const audit = async (page, name) => {
  await page.addScriptTag({ content: axe })
  const { violations } = await page.evaluate(() => window.axe.run({ exclude: [['[role=tablist]']] }, { resultTypes: ['violations'] }))
  const serious = violations.filter((v) => ['serious', 'critical'].includes(v.impact))
  console.log(`${serious.length ? 'FAIL' : 'PASS'}  axe ${name}${serious.map((v) => `\n      ${v.id}: ${v.nodes.length}`).join('')}`)
  return serious.length
}

let failures = 0
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' })
try {
  for (const width of WIDTHS) {
    const page = await browser.newPage({ viewport: { width, height: 900 } })
    await page.goto('http://localhost:5173/app?tab=colloq', { waitUntil: 'networkidle' })
    await page.locator('ul button').first().waitFor()
    await page.screenshot({ path: `${out}/units-${width}.png`, fullPage: true })
    failures += await audit(page, `units ${width}`)
    await page.locator('ul button').first().click()
    await page.locator('ul[aria-label] button').first().click()
    await page.getByRole('button', { name: config.copy.practise }).waitFor()
    await page.screenshot({ path: `${out}/lesson-${width}.png`, fullPage: true })
    failures += await audit(page, `lesson ${width}`)
    await page.close()
  }
} finally {
  await browser.close()
  if (empty && existsSync(placeholder)) rmSync(placeholder)
}
process.exitCode = failures ? 1 : 0
