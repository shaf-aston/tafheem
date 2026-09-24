/**
 * Capture Nahw exercise forms (Google Forms score pages) for transcription.
 *
 *   node scripts/forms-capture.mjs            # every form in nahw_forms/forms.json
 *   node scripts/forms-capture.mjs form-c     # one
 *
 * Writes nahw_forms/<id>/items.json plus one picture per question. Pictures, not
 * OCR: the Arabic sits in images with harakat and underlines that carry the
 * question, and tesseract loses both. A model reads the pictures instead.
 * The respondent's name item is skipped so no personal detail is stored.
 */
import { chromium } from 'playwright'
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const ROOT = new URL('../../backend/data/nahw_forms/', import.meta.url)
const cfg = JSON.parse(readFileSync(new URL('forms.json', ROOT), 'utf8'))
const only = process.argv[2]
const forms = cfg.forms.filter((f) => !only || f.id === only)
if (!forms.length) throw new Error(`no form with id ${only}`)

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: cfg.capture.width, height: 900 }, deviceScaleFactor: cfg.capture.scale })

for (const form of forms) {
  const dir = new URL(`${form.id}/`, ROOT)
  mkdirSync(dir, { recursive: true })
  await page.goto(form.url, { waitUntil: 'networkidle' })

  // Lazy images only load once scrolled past, so walk the page before reading it.
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 120)) }
  })
  await page.waitForTimeout(cfg.capture.settle_ms)

  // Options are listitems too; only the outermost ones are questions or section headers.
  const tops = page.locator('[role="listitem"]:not([role="listitem"] [role="listitem"])')
  const n = await tops.count()
  const items = []
  for (let i = 0; i < n; i++) {
    const el = tops.nth(i)
    const text = (await el.innerText()).trim()
    if (/^\d+ of \d+ points\s*\nName\b/.test(text)) continue
    const key = `q${String(items.length + 1).padStart(3, '0')}`
    await el.scrollIntoViewIfNeeded()
    await el.screenshot({ path: fileURLToPath(new URL(`${key}.png`, dir)) })
    items.push({ key, image: `${key}.png`, text })
  }
  const title = await page.title()
  writeFileSync(new URL('items.json', dir), JSON.stringify({ id: form.id, title, url: form.url, items }, null, 1))
  console.log(form.id, title, items.length, 'items')
}
await browser.close()
