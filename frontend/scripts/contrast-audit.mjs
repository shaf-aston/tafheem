/**
 * Contrast audit: measures what the screen shows, not what the tokens promise.
 *
 *   node scripts/contrast-audit.mjs [report.json]     (APP=http://localhost:5179)
 *   LOOKS=ink WIDTHS=390 SCREENS=home node scripts/contrast-audit.mjs   # narrow a run
 *
 * theme.test.js holds the tokens to 4.5:1, but a component can still put a
 * faint token on a card, or text on a translucent layer. So this opens the real
 * app in every look (theme.json themes.looks) at 390x844 and 1280x800, on Home,
 * every listed tab (lib/tabs.js LISTED), Home with All sections open and with
 * Settings open, and checks every visible text node:
 *   text     WCAG 4.5:1, or 3:1 at >= 24px, or >= 18.66px and bold (700+)
 *   control  border of a button/link/input/select/textarea against its ground, 3:1
 * Effective background: climb ancestors, compositing each translucent
 * background-color over the next one up, until an opaque one (or the canvas).
 * Cannot judge: text over background-image/gradients/canvas/video (flagged
 * `image`, ratio measured on the colour beneath only) and text over another
 * element that is not its ancestor (overlays, pseudo-elements).
 * Also: horizontal overflow, and tap targets under 44x44 (worst 10).
 * Writes JSON to argv[2] and a markdown summary to stdout.
 */
import { chromium } from 'playwright'
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { dirname } from 'node:path'

const APP = process.env.APP ?? 'http://localhost:5179'
const OUT = process.argv[2] ?? '/tmp/claude-0/-home-user-tafheem/63aa7e0c-a3d9-5d26-8892-e806af562f7b/scratchpad/contrast/report.json'
const theme = JSON.parse(readFileSync(new URL('../src/config/theme.json', import.meta.url)))
const HINT_KEY = theme.themes['hint-key']
const pick = (env, all) => (process.env[env] ? process.env[env].split(',') : all)
const LOOKS = pick('LOOKS', Object.keys(theme.themes.looks))
const WIDTHS = pick('WIDTHS', ['390', '1280']).map(Number)
const SIZES = { 390: 844, 1280: 800 }

/** Runs in the page. Returns { fails, tapSmall, overflow, checked }. */
function inPage() {
  // Computed colours can come back as color(srgb ..), oklch(..) etc. (color-mix, modern tokens);
  // a 1x1 canvas turns any of them into plain 0-255 bytes.
  const pen = document.createElement('canvas').getContext('2d', { willReadFrequently: true })
  pen.canvas.width = pen.canvas.height = 1
  const rgba = (s) => {
    pen.clearRect(0, 0, 1, 1); pen.fillStyle = '#000'; pen.fillStyle = s; pen.fillRect(0, 0, 1, 1)
    const [r, g, b, a] = pen.getImageData(0, 0, 1, 1).data
    // Unpremultiply: the canvas stores the alpha-scaled bytes.
    return a ? { r: Math.min(255, r * 255 / a), g: Math.min(255, g * 255 / a), b: Math.min(255, b * 255 / a), a: a / 255 } : { r: 0, g: 0, b: 0, a: 0 }
  }
  const over = (top, under) => { // composite top over an opaque under
    const a = top.a
    return { r: top.r * a + under.r * (1 - a), g: top.g * a + under.g * (1 - a), b: top.b * a + under.b * (1 - a), a: 1 }
  }
  const lin = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4 }
  const lum = (c) => 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b)
  const ratio = (a, b) => { const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x); return (hi + 0.05) / (lo + 0.05) }
  const hex = (c) => '#' + [c.r, c.g, c.b].map((v) => Math.round(v).toString(16).padStart(2, '0')).join('')
  const canvas = rgba(getComputedStyle(document.documentElement).backgroundColor.startsWith('rgba(0, 0, 0, 0)')
    ? getComputedStyle(document.body).backgroundColor : getComputedStyle(document.documentElement).backgroundColor)
  const ground = { r: canvas.a ? canvas.r : 255, g: canvas.a ? canvas.g : 255, b: canvas.a ? canvas.b : 255, a: 1 }

  /** Effective background of el: layers from el up, composited down onto the first opaque one. */
  const backgroundOf = (el) => {
    const layers = []; let image = false
    for (let n = el; n; n = n.parentElement) {
      const cs = getComputedStyle(n)
      if (cs.backgroundImage !== 'none') image = true
      const c = rgba(cs.backgroundColor)
      if (c.a > 0) { layers.push(c); if (c.a >= 1) break }
    }
    let base = layers.length && layers[layers.length - 1].a >= 1 ? layers.pop() : ground
    for (const l of layers.reverse()) base = over(l, base)
    return { color: base, image }
  }
  const selector = (el) => {
    const bits = []
    for (let n = el; n && n !== document.body && bits.length < 3; n = n.parentElement) {
      const cls = [...n.classList].filter((c) => !/[\[\]:/]/.test(c)).slice(0, 2).join('.')
      bits.unshift(n.tagName.toLowerCase() + (n.id ? '#' + n.id : '') + (cls ? '.' + cls : ''))
    }
    return bits.join(' > ')
  }
  const hidden = (el) => {
    for (let n = el; n && n !== document.documentElement; n = n.parentElement) {
      const cs = getComputedStyle(n)
      if (cs.display === 'none' || cs.visibility === 'hidden' || Number(cs.opacity) === 0) return true
      if (n.getAttribute('aria-hidden') === 'true' || n.tagName.toLowerCase() === 'svg' || n.hasAttribute('inert')) return true
    }
    return false
  }
  // A closed <dialog> is display:none and so skipped above; an open one is audited alone-with-page.
  const opacityOf = (el) => { let o = 1; for (let n = el; n; n = n.parentElement) o *= Number(getComputedStyle(n).opacity); return o }

  const fails = []; let checked = 0; let decorative = 0
  for (const el of document.body.querySelectorAll('*')) {
    const own = [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join('').trim()
    if (!own || ['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(el.tagName)) continue
    const box = el.getBoundingClientRect()
    if (!box.width || !box.height || hidden(el)) continue
    const cs = getComputedStyle(el)
    if (opacityOf(el) < 0.15) { decorative++; continue } // faded out on purpose: counted, not judged
    const bg = backgroundOf(el)
    const fg0 = rgba(cs.color)
    const fg = over({ ...fg0, a: fg0.a * opacityOf(el) }, bg.color)
    const px = parseFloat(cs.fontSize); const bold = Number(cs.fontWeight) >= 700
    const need = px >= 24 || (px >= 18.66 && bold) ? 3 : 4.5
    const r = ratio(fg, bg.color); checked++
    if (r < need) fails.push({ kind: 'text', text: own.slice(0, 50), selector: selector(el), fg: hex(fg), bg: hex(bg.color), ratio: +r.toFixed(2), need, image: bg.image, fontPx: px })
  }
  const controls = 'button, a[href], input, select, textarea, [role=button], [role=link]'
  for (const el of document.body.querySelectorAll(controls)) {
    const box = el.getBoundingClientRect(); const cs = getComputedStyle(el)
    if (!box.width || !box.height || hidden(el) || el.type === 'hidden' || cs.borderTopStyle === 'none' || !parseFloat(cs.borderTopWidth)) continue
    const bc = rgba(cs.borderTopColor); if (!bc.a) continue
    const outer = backgroundOf(el.parentElement ?? el).color
    const border = over(bc, outer); const r = ratio(border, outer); checked++
    if (r < 3) fails.push({ kind: 'control', text: (el.getAttribute('aria-label') || el.textContent || el.tagName).trim().replace(/\s+/g, ' ').slice(0, 30), selector: selector(el), fg: hex(border), bg: hex(outer), ratio: +r.toFixed(2), need: 3, image: false })
  }
  const small = []
  for (const el of document.body.querySelectorAll('button, a[href], input, [role=button], [role=tab]')) {
    const b = el.getBoundingClientRect()
    if (!b.width || !b.height || hidden(el) || el.type === 'hidden' || el.matches('a.sr-only')) continue // skip-links are not targets
    if (b.width < 44 || b.height < 44) small.push({ selector: selector(el), text: (el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 30), w: Math.round(b.width), h: Math.round(b.height) })
  }
  small.sort((a, b) => a.w * a.h - b.w * b.h)
  const se = document.scrollingElement
  return { fails, checked, decorative, tapSmall: { count: small.length, worst: small.slice(0, 10) }, overflow: se.scrollWidth > innerWidth ? se.scrollWidth - innerWidth : 0 }
}

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'] })
const probe = await browser.newPage()
await probe.goto(`${APP}/app`, { waitUntil: 'networkidle' })
const ids = await probe.evaluate(async () => (await import('/src/lib/nav/tabs.js')).LISTED.map((t) => t.id))
await probe.close()
const SCREENS = [
  ...ids.map((id) => ({ name: id, path: id === 'home' ? '/app' : `/app/${id}` })),
  { name: 'home+sections', path: '/app', open: 'All sections' },
  { name: 'home+settings', path: '/app', open: 'Settings' },
].filter((s) => !process.env.SCREENS || process.env.SCREENS.split(',').includes(s.name))

const rows = []
for (const look of LOOKS) {
  for (const width of WIDTHS) {
    const ctx = await browser.newContext({ viewport: { width, height: SIZES[width] ?? 800 }, hasTouch: width < 600, reducedMotion: 'reduce' })
    // Choose the look the way a reader does (settings store) plus the early-paint hint.
    await ctx.addInitScript(([hint, id]) => {
      try { localStorage.setItem(hint, id); localStorage.setItem('settings', JSON.stringify({ theme: id })) } catch {}
    }, [HINT_KEY, look])
    for (const s of SCREENS) {
      const page = await ctx.newPage()
      try {
        await page.goto(APP + s.path, { waitUntil: 'networkidle' })
        // Colours are measured at rest: a fade or theme transition in flight reads as near-black.
        await page.addStyleTag({ content: '*,*::before,*::after{transition:none!important;animation:none!important}' })
        await page.waitForTimeout(800)
        if (s.open) {
          // On a phone the tab strip is replaced by the bottom bar; both carry the same label.
          await page.locator(`button[aria-label^="${s.open}"]:visible`).first().click()
          await page.waitForTimeout(800)
        }
        const look_ = await page.evaluate(() => document.documentElement.dataset.theme)
        const res = await page.evaluate(inPage)
        rows.push({ screen: s.name, look, width, applied: look_, ...res })
      } catch (e) {
        rows.push({ screen: s.name, look, width, error: String(e.message).split('\n')[0], fails: [], tapSmall: { count: 0, worst: [] }, overflow: 0, checked: 0 })
      }
      await page.close()
    }
    await ctx.close()
  }
}
await browser.close()
mkdirSync(dirname(OUT), { recursive: true })
writeFileSync(OUT, JSON.stringify(rows, null, 2))

const count = (r, kind) => r.fails.filter((f) => f.kind === kind).length
console.log('| screen | look | width | checked | text fails | control fails | overflow px | taps <44 | decorative skipped | note |\n|---|---|---|---|---|---|---|---|---|---|')
for (const r of rows) {
  const note = r.error ? `ERROR ${r.error}` : r.applied !== r.look ? `look applied: ${r.applied}` : ''
  console.log(`| ${r.screen} | ${r.look} | ${r.width} | ${r.checked} | ${count(r, 'text')} | ${count(r, 'control')} | ${r.overflow} | ${r.tapSmall.count} | ${r.decorative ?? 0} | ${note} |`)
}
// Top failures: de-duplicated by (fg,bg,text) so one bad pair is not 40 lines.
const seen = new Map()
for (const r of rows) for (const f of r.fails) {
  const k = [f.kind, f.fg, f.bg, f.text].join('|')
  if (!seen.has(k)) seen.set(k, { ...f, where: [] })
  seen.get(k).where.push(`${r.screen}/${r.look}/${r.width}`)
}
const top = [...seen.values()].sort((a, b) => a.ratio / a.need - b.ratio / b.need).slice(0, 40)
console.log(`\n${seen.size} distinct failures; worst 40:\n\n| kind | text | selector | fg | bg | ratio | need | img | seen on |\n|---|---|---|---|---|---|---|---|---|`)
for (const f of top) console.log(`| ${f.kind} | ${f.text.replace(/\|/g, '/')} | ${f.selector} | ${f.fg} | ${f.bg} | ${f.ratio} | ${f.need} | ${f.image ? 'yes' : ''} | ${f.where.length} (${f.where[0]}) |`)
console.log(`\nTOTAL fails: ${rows.reduce((n, r) => n + r.fails.length, 0)} | report: ${OUT}`)
