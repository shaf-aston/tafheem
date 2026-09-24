import { chromium } from 'playwright'
const b = await chromium.launch()
const ctx = await b.newContext({ viewport: { width: 390, height: 664 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 })
const p = await ctx.newPage()
await p.goto('http://localhost:5173/', { waitUntil: 'networkidle' })
const info = await p.evaluate(() => {
  const t = document.querySelector('.pin-track'), s = document.querySelector('.pin-sticky')
  const r = t.getBoundingClientRect()
  return { top: r.top + scrollY, h: r.height, stickyH: s.getBoundingClientRect().height, ih: innerHeight, sticky: getComputedStyle(s).position }
})
console.log(info)
for (const f of [0, 0.05, 0.3, 0.6, 0.95]) {
  await p.evaluate(([i, f]) => window.scrollTo(0, i.top + (i.h - innerHeight) * f), [info, f])
  await p.waitForTimeout(700)
  const s = await p.evaluate(() => {
    const st = document.querySelector('.pin-sticky').getBoundingClientRect()
    const fr = document.querySelector('.sd-frame').getBoundingClientRect()
    const sc = document.querySelector('.sd-diagram .tk-scroller')
    return { stickyTop: Math.round(st.top), frameW: Math.round(fr.width), frameH: Math.round(fr.height), caption: document.querySelector('.pin-caption h3').textContent,
      on: document.querySelectorAll('.sd-diagram [data-on]').length, scrollW: sc?.scrollWidth, clientW: sc?.clientWidth, zoom: sc && getComputedStyle(sc).zoom }
  })
  console.log(f, JSON.stringify(s))
  await p.screenshot({ path: `${process.env.TEMP}/pin-${f}.png` })
}
await b.close()
