/**
 * Drive the command line and the launcher in a real browser.
 *
 *   node scripts/probe-command.mjs
 *
 * Not a test. The unit tests prove the classifier; this proves that typing into
 * the running page actually lands on the right tab with the right thing loaded,
 * which is the only place a wrong selector or a dead handler shows itself.
 */
import { chromium } from 'playwright'

const SHOT = process.env.PROBE_SHOT ?? 'probe-command.png'

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } })

let problems = 0
const note = (...parts) => console.log(...parts)
page.on('pageerror', (e) => { problems++; note('PAGEERROR', e.message.slice(0, 300)) })
page.on('requestfailed', (r) => { problems++; note('FAILED', r.url(), r.failure()?.errorText) })
page.on('response', async (r) => {
  if (!r.url().includes('/api/') || r.status() < 400) return
  problems++
  note('HTTP', r.status(), r.url(), (await r.text().catch(() => '')).slice(0, 300))
})

const check = (label, ok, detail = '') => {
  if (!ok) problems++
  note(ok ? 'OK  ' : 'BAD ', label, detail)
}

// Both surfaces hold the same box now, and the launcher's stays in the page
// while shut, so every locator here says which of the two it means.
const bar = page.locator('.cb > .cb-field .cb-input')
const tabOf = () => page.evaluate(() => new URL(location.href).searchParams.get('tab'))

await page.goto('http://localhost:5173/?tab=nahw', { waitUntil: 'networkidle' })

// The header is a pen and a bar now, not a title. The heading still exists for
// a screen reader, so what is checked is the space it takes on screen: text
// read aloud but not painted is the point, and its own text still reads back.
const headingBox = await page.locator('header h1').first().boundingBox()
check('title takes no room on screen', (headingBox?.width ?? 99) <= 2,
  `${Math.round(headingBox?.width ?? -1)}px wide`)
check('pen badge is there', await page.locator('.pen-badge').isVisible())

// Ctrl+K from anywhere.
await page.keyboard.press('Control+k')
check('Ctrl+K focuses the bar', await bar.evaluate((el) => el === document.activeElement))

// The motion tokens are plain numbers, so a duration has to be built with
// calc(... * 1ms). Written as a bare var it is not a duration, the browser drops
// the whole line, and everything animates instantly while looking like it should
// not. Ask the browser what it actually ended up with.
const barMotion = await page.locator('.cb > .cb-field').evaluate((el) => getComputedStyle(el).transitionDuration)
check('the bar really transitions', !/^0s/.test(barMotion), barMotion)

// An ayah address.
await bar.fill('2:255')
await page.waitForTimeout(150)
check('ayah is offered', (await page.locator('.cb-row').first().innerText()).includes('2:255'))
await page.keyboard.press('Enter')
await page.waitForTimeout(4000)
check('ayah opened the Quran tab', (await tabOf()) === 'quran')
const body = await page.innerText('body')
check('the ayah itself loaded', body.includes('255') && (await page.locator('.gloss-word, .word').count()) > 0)

// Ghost completion, then Tab to accept it.
await page.keyboard.press('Control+k')
await bar.fill('dic')
await page.waitForTimeout(120)
check('ghost completes the tab name', (await page.locator('.cb > .cb-field .cb-ghost').innerText()).includes('tionary'))
await page.keyboard.press('Tab')
check('Tab accepts the ghost', (await bar.inputValue()) === 'dictionary')
await page.keyboard.press('Enter')
await page.waitForTimeout(600)
check('it went to the Dictionary', (await tabOf()) === 'dict')

// A root, with the @ prefix.
await page.keyboard.press('Control+k')
await bar.fill('@كتب')
await page.waitForTimeout(150)
const rootRows = await page.locator('.cb-row').count()
check('a root offers more than one place', rootRows >= 3, `${rootRows} rows`)
check('the rail is drawn', (await page.locator('.cb-rail-chip').count()) === 7)

// Focus never leaves the box while the arrows walk the list, so the box has to
// name the current row by id or a screen reader is told nothing at all.
const pointsAt = await bar.getAttribute('aria-activedescendant')
const namedRow = pointsAt ? await page.locator(`#${pointsAt}`).count() : 0
check('the highlighted row is announced', namedRow === 1, pointsAt ?? 'nothing pointed at')
check('the list is really a listbox of options',
  (await page.locator('[role="listbox"] > [role="group"] > * > * > [role="option"]').count()) > 0)
await page.screenshot({ path: SHOT.replace('.png', '-bar.png') })
await page.keyboard.press('Enter')
await page.waitForTimeout(3000)
check('the root landed in the Dictionary', (await tabOf()) === 'dict')

// The catch-all: a sentence must actually arrive, not be silently dropped.
await page.keyboard.press('Control+k')
await bar.fill('ذهب الولد إلى المدرسة')
await page.waitForTimeout(200)
check('a sentence is offered to the analyser',
  (await page.locator('.cb-row').last().innerText()).includes('Analyse')
  || (await page.locator('.cb-row').count()) > 0)
await page.keyboard.press('Enter')
await page.waitForTimeout(3500)
check('the sentence route opened Nahw', (await tabOf()) === 'nahw')
const carried = await page.locator('#iraab-input').inputValue().catch(() => '')
check('the sentence arrived with it', carried.includes('الولد'), JSON.stringify(carried))

// Nothing typed is still not nothing offered.
await page.keyboard.press('Control+k')
await bar.fill('what is a mubtada')
await page.waitForTimeout(150)
check('plain English still lands somewhere', (await page.locator('.cb-row').count()) > 0)
await page.keyboard.press('Escape')

// The launcher, opened from a page that is not the first tab: it has to arrive
// turned to where the reader already is, in that tab's colour.
await page.goto('http://localhost:5173/?tab=daleel', { waitUntil: 'networkidle' })
await page.locator('.pen-badge').click()
await page.waitForTimeout(1400)
check('the launcher opened', await page.locator('.sh-orbit').isVisible())
check('all seven tabs orbit', (await page.locator('.sh-sat').count()) === 7)
check('it opens on the tab you are in',
  (await page.locator('.sh-sat[data-selected] .sh-sat-label').innerText()) === 'Daleel')

const satMotion = await page.locator('.sh-sat').first()
  .evaluate((el) => getComputedStyle(el).animationDuration)
check('the satellites really arrive', !/^0s/.test(satMotion), satMotion)

// Hovering must light a satellite, never move one. Turning the ring towards the
// pointer slides the next satellite under it, which hovers itself: the ring then
// chases the cursor and never settles. Hold the mouse still and watch.
const resting = await page.locator('.sh-sat').nth(2).boundingBox()
await page.mouse.move(resting.x + resting.width / 2, resting.y + resting.height / 2)
const watched = []
for (let i = 0; i < 12; i++) {
  await page.waitForTimeout(120)
  watched.push(await page.locator('.sh-sat[data-selected] .sh-sat-label').innerText())
}
const drifted = watched.filter((label, i) => i > 0 && label !== watched[i - 1]).length
check('the ring holds still under a still pointer', drifted === 0, `${drifted} changes in 1.4s`)
await page.screenshot({ path: SHOT.replace('.png', '-orbit.png') })

const selectedBefore = await page.locator('.sh-sat[data-selected] .sh-sat-label').innerText()
await page.keyboard.press('ArrowRight')
await page.waitForTimeout(500)
const selectedAfter = await page.locator('.sh-sat[data-selected] .sh-sat-label').innerText()
check('the arrows spin the ring', selectedBefore !== selectedAfter, `${selectedBefore} then ${selectedAfter}`)

// The orb holds the header's own box, not a lookalike: same glass, same rounded
// edge, same grey completion. Two fields are on the page now, the header's one
// behind the dialog, so everything here is asked of the one inside the orb.
const orbField = page.locator('.sh-orb .cb-field')
check('the orb has the search box, glass and all',
  (await orbField.locator('.cb-glass').count()) === 1)
const orbRadius = await orbField.evaluate((el) => getComputedStyle(el).borderRadius)
check('its corners are rounded', parseFloat(orbRadius) > 2, orbRadius)

// One ring, on the box, not a second square one drawn on the bare input inside
// it. Focus still has to be visible, so both halves are asked: the inner ring
// gone, and the box itself lit.
const rings = await orbField.evaluate((el) => ({
  inner: getComputedStyle(el.querySelector('.cb-input')).outlineStyle,
  box: getComputedStyle(el).boxShadow,
}))
check('the focused box wears one ring, and it is round',
  rings.inner === 'none' && rings.box !== 'none', JSON.stringify(rings).slice(0, 90))

// The pen in the middle dances. The tokens it is built from are plain numbers,
// so a bare var would leave it standing still while the CSS looks right.
const penStep = await page.locator('.sh-orb .qalam-pen')
  .evaluate((el) => getComputedStyle(el).animationName + ' ' + getComputedStyle(el).animationDuration)
check('the pen in the middle dances', /qalam-dance \d*\.?\d+s/.test(penStep)
  && !/ 0s$/.test(penStep), penStep)

const orbInput = page.locator('.sh-orb .cb-input')
await orbInput.fill('qui')
await page.waitForTimeout(150)
check('the orb completes like the header does',
  (await page.locator('.sh-orb .cb-ghost').innerText()).includes('z'))
// The two halves part when there is something to show, and which side each
// takes follows the language. Measured rather than eyeballed: the ring must end
// up on the correct side, the answers opposite, and the pair still centred on
// the window, which is what a wrong sign in the shift maths would break.
const sides = async () => {
  const ring = await page.locator('.sh-ring').boundingBox()
  const panel = await page.locator('.sh-panel').boundingBox()
  const middle = (await page.viewportSize()).width / 2
  return {
    ring: ring.x + ring.width / 2 - middle,
    panel: panel.x + panel.width / 2 - middle,
    pair: Math.round(((Math.min(ring.x, panel.x)
      + Math.max(ring.x + ring.width, panel.x + panel.width)) / 2) - middle),
    tall: Math.round(panel.height),
  }
}
await orbInput.fill('quiz')
await page.waitForTimeout(700)
const english = await sides()
check('English puts the ring left and the answers right',
  english.ring < -100 && english.panel > 100, JSON.stringify(english))
check('and the two of them together stay centred', Math.abs(english.pair) <= 2,
  `${english.pair}px off`)
// The panel used to be squeezed to a sliver against the bottom of the window.
check('the answers get their full height', english.tall > 150, `${english.tall}px`)

await orbInput.fill('كتب')
await page.waitForTimeout(700)
const arabic = await sides()
check('Arabic swaps the two of them over',
  arabic.ring > 100 && arabic.panel < -100, JSON.stringify(arabic))
check('the letter strip moves to the ring side too',
  await page.locator('.sh-panel .cb-results')
    .evaluate((el) => getComputedStyle(el).flexDirection) === 'row-reverse')

await orbInput.fill('quiz')
await page.waitForTimeout(200)
check('typing narrows the ring', (await page.locator('.sh-sat[data-dim]').count()) > 0)
await page.keyboard.press('Enter')
await page.waitForTimeout(800)
// The dialog stays in the page when shut, so "closed" means it stopped being
// drawn, not that it stopped existing.
check('the launcher navigated', (await tabOf()) === 'quiz')
check('the launcher closed behind it', !(await page.locator('.sh-orbit').isVisible()))

// Esc closes it with nothing typed.
await page.locator('.pen-badge').click()
await page.waitForTimeout(500)
await page.keyboard.press('Escape')
await page.waitForTimeout(500)
check('Esc closes the launcher', !(await page.locator('.sh-orbit').isVisible()))

await page.screenshot({ path: SHOT, fullPage: true })
await browser.close()

console.log(problems ? `PROBLEMS: ${problems}` : 'CLEAN')
process.exit(problems ? 1 : 0)
