/**
 * The home-screen icons, drawn from public/favicon.svg: `node scripts/make-icons.mjs`.
 *
 * Android wants 192 and 512 PNGs (an SVG alone does not make the app installable
 * everywhere) plus a maskable one it may crop to a circle or squircle, so the
 * mark sits in the middle 60% on a full-bleed plate. iOS reads one 180 PNG
 * (apple-touch-icon) and rounds its corners itself, so that one is full-bleed too.
 */
import { readFileSync } from 'node:fs'
import { chromium } from 'playwright'

const PLATE = '#0c1018'
const svg = readFileSync(new URL('../public/favicon.svg', import.meta.url), 'utf8')
// The favicon's own rounded plate is dropped for the full-bleed ones: the OS rounds them.
const mark = svg.replace(/<rect[^>]*\/>/, '').replace(/<svg[^>]*>/, '').replace('</svg>', '')

const ICONS = [
  { file: 'icon-192.png', size: 192, plate: false },
  { file: 'icon-512.png', size: 512, plate: false },
  { file: 'icon-maskable-512.png', size: 512, plate: true, inset: 0.6 },
  { file: 'apple-touch-icon.png', size: 180, plate: true, inset: 0.78 },
]

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM ?? '/opt/pw-browsers/chromium' })
for (const { file, size, plate, inset = 1 } of ICONS) {
  const page = await browser.newPage({ viewport: { width: size, height: size } })
  const body = plate
    ? `<rect width="24" height="24" fill="${PLATE}"/><g transform="translate(${(24 * (1 - inset)) / 2} ${(24 * (1 - inset)) / 2}) scale(${inset})">${mark}</g>`
    : svg.replace(/<svg[^>]*>/, '').replace('</svg>', '')
  await page.setContent(`<body style="margin:0;background:transparent"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}">${body}</svg></body>`)
  await page.screenshot({ path: new URL(`../public/${file}`, import.meta.url).pathname, omitBackground: !plate })
  await page.close()
}
await browser.close()
