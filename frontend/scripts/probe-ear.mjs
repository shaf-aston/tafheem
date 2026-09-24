/**
 * The whole path, with a real recitation and a real ear: recordings of
 * al-Fatihah are the microphone, the page records them, the backend hears
 * them, and the page marks the words.
 *
 *   EAR=http://127.0.0.1:8011 node scripts/probe-ear.mjs
 *
 * Knobs, all by environment:
 *   EAR    the backend to hear it; 8011 started with RECITATION_HOSTED=false
 *          proves the local ear, 8000 proves the app as configured
 *   CLIPS  everyayah clip numbers, comma separated; default is 1:5 to 1:7,
 *          which also proves the page finds its own start. 001001,...,001007
 *          is the whole page
 *   GAP_S  seconds of breath between clips, default 1. Zero is no human: the
 *          clips run into each other and the windows cut mid-word
 *   QUIET  how much quieter to play them, in decibels, default 0. Somebody
 *          reciting softly or sitting back from the microphone: -30 is about a
 *          thirtieth of the loudness, and used to reach the page as nothing
 *   VIEW   phone for a phone-sized screen
 *   LEVEL  beginner or standard: the checking level the page uses
 *   JUMP   a clip in CLIPS, e.g. 001005: just before it plays, its first word
 *          is pressed while still recording, as a reciter skipping ahead does;
 *          the words before it must then be neither said nor accused
 *   DUMP   a directory; every recording the page sends is saved there as webm,
 *          which is how a lost word is traced to the page or to the ear
 *
 * The mp3s must be under public/_recite/ while it runs; they never belong in
 * the repo. Reciting is patient about silence, so Stop is pressed here once
 * the clips have ended and a last window has gone by. The model's own
 * misreadings are allowed to show: hiding them would make this lie.
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { chromium } from 'playwright'

const EAR = process.env.EAR ?? 'http://127.0.0.1:8011'
// Where the dev server is. A knob because vite binds whatever host it was
// started with, and a run started plainly listens on ::1 alone, which this
// address does not reach.
const APP = process.env.APP ?? 'http://127.0.0.1:5173'
const CLIPS = (process.env.CLIPS ?? '001005,001006,001007').split(',')
const GAP_S = Number(process.env.GAP_S ?? 1)
const QUIET_DB = Number(process.env.QUIET ?? 0)
const DUMP = process.env.DUMP
const JUMP = process.env.JUMP
const LEVEL = process.env.LEVEL ?? 'standard'
const viewport = process.env.VIEW === 'phone' ? { width: 390, height: 844 } : { width: 1280, height: 1000 }
// The first word of the first clip, as the page counts words: 1:1 to 1:4 is 15 words.
const FIRST = { '001001': 0, '001002': 4, '001003': 8, '001004': 10, '001005': 13, '001006': 17, '001007': 20 }
const START = FIRST[JUMP ?? CLIPS[0]] ?? 0
const AYAH = Number((JUMP ?? CLIPS[0]).slice(3))

const results = []
const check = (name, pass, detail = '') => {
  results.push(pass)
  console.log(`${pass ? 'PASS' : 'FAIL'}  ${name}${detail ? `  (${detail})` : ''}`)
}

const browser = await chromium.launch({
  args: ['--use-fake-ui-for-media-stream', '--autoplay-policy=no-user-gesture-required'],
})
const page = await browser.newPage({ viewport, permissions: ['microphone'] })
page.on('pageerror', (e) => console.log('PAGEERROR', e.message.slice(0, 200)))
page.on('console', (m) => { if (m.type() === 'error') console.log('CONSOLE', m.text().slice(0, 200)) })

await page.addInitScript((level) => {
  localStorage.setItem('settings', JSON.stringify({ 'reciting-level': level }))
}, LEVEL)

// The microphone: the clips decoded and played one after another, a breath apart.
await page.addInitScript(({ clips, gap, quiet }) => {
  navigator.mediaDevices.getUserMedia = async () => {
    const ctx = new AudioContext()
    const out = ctx.createMediaStreamDestination()
    // A quieter reciter, through a gain the page cannot see, exactly as a soft
    // voice reaches a real microphone.
    const softer = ctx.createGain()
    softer.gain.value = 10 ** (quiet / 20)
    softer.connect(out)
    let at = ctx.currentTime + 1
    window.__clipStarts = {}
    // When each clip's sound truly ends, on the wall clock, so the lag before
    // the page notices the pause can be measured instead of assumed.
    window.__clipEnds = []
    for (const clip of clips) {
      window.__clipStarts[clip] = at - ctx.currentTime
      const bytes = await (await fetch(`/_recite/${clip}.mp3`)).arrayBuffer()
      const buffer = await ctx.decodeAudioData(bytes)
      const source = ctx.createBufferSource()
      source.buffer = buffer
      source.connect(softer)
      source.start(at)
      window.__clipEnds.push(Date.now() + (at + buffer.duration - ctx.currentTime) * 1000)
      at += buffer.duration + gap
    }
    window.__micEnds = at - ctx.currentTime
    return out.stream
  }
}, { clips: CLIPS, gap: GAP_S, quiet: QUIET_DB })

// Every listen goes to the ear under test, everything else to the dev server.
const heard = []
// Per reading, how many page words the ear checked by sound, and how long it
// took to come back. Half the complaint was how long a mark takes to appear,
// so it is measured here rather than judged by eye.
const checked = []
const waited = []
// Readings the page gave up on because it already knew they were out of date.
let gaveUp = 0
const t0 = Date.now()
await page.route('**/api/listen**', async (route) => {
  const url = new URL(route.request().url())
  if (DUMP) {
    // Multipart: the webm sits between the first blank line and the last boundary.
    const body = route.request().postDataBuffer()
    const from = body.indexOf('\r\n\r\n') + 4
    const to = body.lastIndexOf('\r\n--')
    writeFileSync(`${DUMP}/sent-${String(heard.length + 1).padStart(2, '0')}.webm`, body.subarray(from, to))
  }
  const asked = Date.now()
  // Two minutes, because the ear on this machine is slow and queues, and the
  // default half minute failed the probe rather than measuring it. The page
  // gives up on a reading it knows is out of date, and the browser closing
  // ends any still in flight; neither is a failure, so neither is reported as
  // one, and a reading nobody waited for is not timed either.
  try {
    const got = await route.fetch({ url: `${EAR}${url.pathname}${url.search}`, timeout: 120000 })
    const body = await got.text()
    const isCheck = url.pathname.endsWith('/check')
    // Timed for words only: a mark appears when the words do.
    if (!isCheck) waited.push(Date.now() - asked)
    try {
      const answer = JSON.parse(body)
      // Sureness comes back on its own request, /api/listen/check.
      if (isCheck) checked.push(Object.values(answer.sure ?? {}).flat().filter((s) => s != null).length)
      else heard.push(answer.text)
    } catch { heard.push(body.slice(0, 80)) }
    if (!isCheck) console.log(`  reading ${heard.length} at ${Math.round((Date.now() - t0) / 1000)}s,`
      + ` ${(waited.at(-1) / 1000).toFixed(1)}s to answer: ${heard.at(-1)}`)
    await route.fulfill({ response: got, body })
  } catch {
    gaveUp += 1
  }
})

// Not networkidle: the page keeps asking the backend how it is, so it never
// falls idle, and waiting for that timed the probe out instead of running it.
await page.goto(`${APP}/?tab=mem`, { waitUntil: 'domcontentloaded' })
await page.getByRole('button', { name: 'Recite it' }).click({ timeout: 30000 })
await page.waitForTimeout(500)
await page.getByRole('button', { name: 'Start reciting', exact: true }).click()

// The clips are still being decoded when the button is pressed; read the
// length once they are. Reading it early once cut a whole-page run off at 42s.
await page.waitForFunction(() => window.__micEnds != null)
const ends = await page.evaluate(() => window.__micEnds)
let waitedS = 0
if (JUMP) {
  const jumpAt = await page.evaluate((clip) => window.__clipStarts[clip], JUMP)
  await page.waitForTimeout((jumpAt - 0.5) * 1000)
  waitedS = jumpAt - 0.5
  await page.locator('button[aria-label^="start reciting from"]').nth(START).click()
  const still = await page.getByRole('button', { name: 'Stop', exact: true }).count()
  check('a word can be pressed while reciting, and reciting carries on', still > 0)
}
// The clips, then one more window so the tail is heard and settled.
await page.waitForTimeout((ends + 12 - waitedS) * 1000)
const stop = page.getByRole('button', { name: 'Stop', exact: true })
if (await stop.count()) await stop.click()
else console.log('  the page stopped by itself once the clips fell quiet')
await page.waitForTimeout(3000)

const hint = page.getByText(/following you from|listening for where you are|tap a word to start/)
const line = await hint.first().innerText().catch(() => '')
check('the ear was asked', heard.length > 0, `${heard.length} readings, ${gaveUp} given up on`)
check('it checked words by sound', checked.some((n) => n > 0), `${checked.join(', ')} words per reading, ${LEVEL}`)
check(`it worked out it was 1:${AYAH} by itself`, new RegExp(`following you from\\s*${AYAH}`).test(line), line.trim())

const words = page.locator('button[aria-label^="start reciting from"]')
const total = await words.count()
let said = 0
let above = 0
let aboveSaid = 0
for (let i = 0; i < total; i += 1) {
  const word = words.nth(i)
  if (i < START) {
    above += await word.locator('span[style*="--danger"]').count()
    aboveSaid += await word.locator('span[style*="--text-dim"]').count()
  }
  else said += await word.locator('span[style*="--text-dim"]').count()
}
const covered = await page.locator('[aria-label="a word to say from memory"]').count()
check('most words recited are marked said', said >= (total - START) * 0.75, `${said} of ${total - START} said`)
check('the words above the start are not accused', above === 0, `${above} accused`)
if (JUMP) check('what was recited before the jump is forgotten', aboveSaid === 0, `${aboveSaid} still said`)
check('nothing stays covered but the ear\'s own slips', covered <= 1, `${covered} still covered`)

// Orange means "I cannot tell". A word printed beside an orange one is the
// transcript's guess, and the transcript is the part that gets it wrong: a
// perfect al-Fatihah showed the first word of 1:1 beside the last word of 1:1.
const named = await page.locator('[title="what the microphone heard"][style*="--warn"]').count()
check('no doubtful word names a word', named === 0, `${named} named`)

// The strictness dial, used the way a reciter would: it sits on the reciting
// strip, it shows which level is on, and pressing another one re-marks the page
// there and then, without reciting anything again. Clicked rather than assumed,
// because a control that renders and does nothing looks identical in a test.
const dial = page.getByRole('group', { name: 'Checking level' })
const onNow = await dial.getByRole('button', { pressed: true }).innerText().catch(() => '')
check('the checking level is on the reciting strip', onNow.toLowerCase() === LEVEL, onNow)
const other = LEVEL === 'standard' ? 'Beginner' : 'Standard'
await dial.getByRole('button', { name: other, exact: true }).click()
await page.waitForTimeout(300)
const swapped = await dial.getByRole('button', { pressed: true }).innerText()
const stillSaid = await page.locator('button[aria-label^="start reciting from"] span[style*="--text-dim"]').count()
check(`pressing ${other} changes the level and keeps the page marked`,
  swapped === other && stillSaid > 0, `${swapped}, ${stillSaid} still said`)

const middle = waited.length ? [...waited].sort((a, b) => a - b)[waited.length >> 1] : 0
console.log(`\n  a reading came back in ${(middle / 1000).toFixed(1)}s typically,`
  + ` ${(Math.max(...waited, 0) / 1000).toFixed(1)}s at worst, over ${waited.length} readings`)

// How long after a clip's last sound the page cut the recording there. The
// page stamps each cut in the journal; a cut more than 3s late is another pause.
const clipEnds = await page.evaluate(() => window.__clipEnds)
const cuts = readFileSync('../logs/recite-journal.jsonl', 'utf8').trim().split('\n').map((l) => JSON.parse(l))
  .filter((e) => e.kind === 'window.cut' && e.detail?.why === 'pause').map((e) => Date.parse(e.at))
const lags = clipEnds.map((end) => cuts.find((cut) => cut > end - 300) - end).filter((ms) => ms < 3000).sort((a, b) => a - b)
if (lags.length) console.log(`  a pause was noticed ${(lags[lags.length >> 1] / 1000).toFixed(2)}s after the sound ended, typically`
  + ` (${lags.map((ms) => (ms / 1000).toFixed(2)).join(', ')})`)

await page.screenshot({ path: process.env.SHOT ?? 'probe-ear.png', fullPage: true })
await browser.close()
console.log(results.every(Boolean) ? '\nall passed' : '\nsomething failed')
process.exit(results.every(Boolean) ? 0 : 1)
