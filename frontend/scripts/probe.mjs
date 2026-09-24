/**
 * Drive the running app in a real browser and report what it actually did.
 *
 *   node scripts/probe.mjs                 # the Quran tab, look up 2:21
 *   node scripts/probe.mjs quran 2 21
 *   node scripts/probe.mjs back            # the back arrow, on the Sarf tab
 *
 * Not a test. The test suite proves the parts; this proves the running page,
 * which is the only place a broken request, a crashed render or a bad layout
 * shows itself. Run it before saying a UI change works.
 *
 * It prints every console message, every uncaught error, and every failed or
 * 4xx/5xx call to the backend, then writes a full-page screenshot.
 */
import { chromium } from 'playwright'

const [tab = 'quran', surah = '2', ayah = '21'] = process.argv.slice(2)
const SHOT = process.env.PROBE_SHOT ?? 'probe.png'

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } })

let problems = 0
page.on('console', (m) => console.log('CONSOLE', m.type(), m.text().slice(0, 300)))
page.on('pageerror', (e) => { problems++; console.log('PAGEERROR', e.message.slice(0, 300)) })
page.on('requestfailed', (r) => { problems++; console.log('FAILED', r.url(), r.failure()?.errorText) })
page.on('response', async (r) => {
  if (!r.url().includes('/api/')) return
  if (r.status() < 400) return
  problems++
  console.log('HTTP', r.status(), r.url(), (await r.text().catch(() => '')).slice(0, 400))
})

await page.goto(`http://localhost:5173/?tab=${tab === 'back' || tab === 'bab' ? 'sarf' : tab}`, { waitUntil: 'networkidle' })

// The back arrow, watched rather than trusted. Going back is a return to a page
// already read, so the panel must stay put: no node replaced under #tabpanel
// (a replacement is a remount, and it replays the entrance fade over the whole
// column), and no dip in the page height (the answer must not be cleared while
// the previous word is fetched again). Both used to happen, and together they
// read as the whole screen flashing. See lib/useArrival.
if (tab === 'back') {
  const words = page.locator('button:has-text("to enter"), button:has-text("to sit")')
  await words.first().click()
  await page.waitForTimeout(1500)
  await words.nth(1).click()
  await page.waitForTimeout(1500)

  const watch = await page.evaluate(() => {
    const panel = document.getElementById('tabpanel')
    const seen = { replaced: 0, min: panel.scrollHeight, before: panel.scrollHeight }
    const obs = new MutationObserver((records) => {
      for (const one of records) if (one.target === panel) seen.replaced += 1
      seen.min = Math.min(seen.min, panel.scrollHeight)
    })
    obs.observe(panel, { childList: true, subtree: true, characterData: true })
    window.__watch = { seen, obs }
    return seen.before
  })

  await page.goBack()
  await page.waitForTimeout(1500)
  const back = await page.evaluate(() => {
    window.__watch.obs.disconnect()
    return { ...window.__watch.seen, after: document.getElementById('tabpanel').scrollHeight,
             word: document.getElementById('sarf-input').value }
  })

  const kept = back.replaced === 0 && back.min >= back.before
  if (!kept) problems++
  console.log('BACK', kept ? 'held the page' : 'FLASHED',
    '| panel replaced', back.replaced, 'times | height', watch, '->', back.min, '->', back.after,
    '| box now', back.word)
}

if (tab === 'quran') {
  await page.fill('#surah-input', surah)
  await page.fill('#ayah-input', ayah)
  await page.getByRole('button', { name: /Look up ayah/i }).click()
  // The deep analysis is the slow path; give it room before judging the page.
  await page.waitForTimeout(6000)

  // The reading view, and the hover gloss in it: open the surah, point at the
  // second word of the first ayah, and read back what appeared.
  await page.getByRole('button', { name: /Read all of surah/i }).click()
  await page.waitForTimeout(2500)
  const word = page.locator('.gloss-word').nth(1)
  const words = await page.locator('.gloss-word').count()
  await word.hover()
  await page.waitForTimeout(500)
  const tip = word.locator('.gloss-tip')
  console.log('GLOSS words', words, '| second word', (await word.innerText()).trim(),
    '| its english', (await tip.innerText()).trim(),
    '| shown', await tip.evaluate((e) => getComputedStyle(e).opacity))
  await page.screenshot({ path: SHOT.replace('.png', '-reader.png') })
}

// Bab tags: proves the Lane+Wiktionary milestone without eyeballing a
// screenshot. Both books cited on one reading, a second bab shown as its own
// reading, a Lane-only word, and a word neither book records showing no table.
if (tab === 'bab') {
  // Read only VerbFormTag's own markup, not the whole page: SourceFooter lists
  // every source used anywhere on the Sarf tab (Lane and Wiktionary both) at
  // the foot of every word, so a body-wide text search would pass regardless
  // of which badges this particular word actually rendered.
  const sarfWord = async (word) => {
    await page.fill('#sarf-input', word)
    await page.getByLabel('Arabic word').press('Enter')
    await page.waitForTimeout(1500)
    return page.locator('[data-testid="bab-readings"]').innerText()
  }
  // SourceBadge prints a verified source's own label, unabbreviated: "Lane's
  // Arabic-English Lexicon" and "Wiktionary", never a short "Lane" form.
  const katab = await sarfWord('كتب')
  const katabLabelOk = katab.includes('باب نَصَرَ يَنْصُرُ')
  const katabLaneOk = katab.includes("Lane's Arabic-English Lexicon")
  const katabWiktionaryOk = katab.includes('Wiktionary')
  if (!katabLabelOk) problems++
  if (!katabLaneOk) problems++
  if (!katabWiktionaryOk) problems++
  console.log('SARF كتب', katabLabelOk ? 'label ok' : 'LABEL MISSING',
    '| Lane badge', katabLaneOk ? 'ok' : 'MISSING',
    '| Wiktionary badge', katabWiktionaryOk ? 'ok' : 'MISSING')

  const samia = await sarfWord('سمع')
  const samiaOk = samia.includes('باب سَمِعَ يَسْمَعُ')
  if (!samiaOk) problems++
  console.log('SARF سمع', samiaOk ? 'label ok' : 'LABEL MISSING')

  // ثمل: both books name three babs, two pasts; each is its own reading.
  const thamil = await sarfWord('ثمل')
  const thamilOk = thamil.includes('باب ضَرَبَ يَضْرِبُ') && thamil.includes('باب سَمِعَ يَسْمَعُ')
  if (!thamilOk) problems++
  console.log('SARF ثمل', thamilOk ? 'both bab readings shown' : 'A READING IS MISSING')

  // دغش: a sound root neither book records. Never-guess line, and no table at
  // all (a four-letter root like زهزه would still get its one table by shape).
  const zahza = await sarfWord('دغش')
  const zahzaNoteOk = zahza.includes('No dictionary here records')
  const zahzaNoTableOk = !(await page.locator('table').count())
    && (await page.getByLabel('Verb form').inputValue()) === ''
  if (!zahzaNoteOk) problems++
  if (!zahzaNoTableOk) problems++
  console.log('SARF دغش', zahzaNoteOk ? 'not-recorded line shown' : 'LINE MISSING',
    '| table', zahzaNoTableOk ? 'absent, as it should be' : 'STILL RENDERED')

  // كدح: Lane names a~a, Wiktionary has no verb for it at all; Lane alone,
  // no Wiktionary badge, replacing the old CAMeL-guess path this milestone
  // removes.
  const kadaha = await sarfWord('كدح')
  const kadahaLabelOk = kadaha.includes('باب فَتَحَ يَفْتَحُ')
  const kadahaLaneOk = kadaha.includes("Lane's Arabic-English Lexicon")
  const kadahaNoWiktionary = !kadaha.includes('Wiktionary')
  if (!kadahaLabelOk) problems++
  if (!kadahaLaneOk) problems++
  if (!kadahaNoWiktionary) problems++
  console.log('SARF كدح', kadahaLabelOk ? 'label ok' : 'LABEL MISSING',
    '| Lane badge', kadahaLaneOk ? 'ok' : 'MISSING',
    '| Wiktionary badge', kadahaNoWiktionary ? 'correctly absent' : 'SHOULD NOT BE THERE')
}

console.log('BODY', (await page.innerText('body')).slice(0, 1200).split('\n').join(' | '))
await page.screenshot({ path: SHOT, fullPage: true })
await browser.close()

console.log(problems ? `PROBLEMS: ${problems}` : 'CLEAN')
process.exit(problems ? 1 : 0)
