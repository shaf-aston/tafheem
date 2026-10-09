/**
 * The lantern backdrop: soft out-of-focus lights drifting on a dark warm
 * ground behind every tab, a share of them in the tab's colour (--c, set by
 * App). Under the lights, a few large faint Arabic letters drift in that same
 * colour (theme.json's marks group), drawn on this canvas so there is one
 * surface and one loop.
 *
 * Mounted once by App, first, so it paints under everything. The arithmetic
 * is lib/bokeh.js and every knob is theme.json's lights group; this file only
 * draws. It stops, leaving the last frame, when the Animations setting drives
 * --motion-scale to 0, under prefers-reduced-motion, or while the tab is
 * hidden, so it costs nothing when nobody can see it move. It also holds
 * still, tint change included, for the moment a tab switches (lib/backdropHold).
 * data-frames counts
 * drawn frames, which is how a probe proves it stopped.
 */
import { useEffect, useRef } from 'react'

import { pickColor, seed, seedMarks, step, stepMarks } from '../lib/bokeh'
import { heldFor } from '../lib/backdropHold'

const reduced = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches

function readKnobs(style) {
  const num = (name) => parseFloat(style.getPropertyValue(`--lights-${name}`))
  const text = (name) => style.getPropertyValue(`--lights-${name}`).trim()
  return {
    count: num('count'),
    sizeMin: num('size-min-px'),
    sizeMax: num('size-max-px'),
    speed: num('speed'),
    alpha: num('alpha'),
    tint: num('tint'),
    groundTop: text('ground-top'),
    groundBottom: text('ground-bottom'),
    colors: text('colors').split(',').map((c) => c.trim()),
  }
}

function readMarks(style) {
  const num = (name) => parseFloat(style.getPropertyValue(`--marks-${name}`))
  const text = (name) => style.getPropertyValue(`--marks-${name}`).trim()
  // The size knobs are rem; the canvas works in px.
  const rem = parseFloat(style.fontSize)
  return {
    count: num('count'),
    sizeMin: num('size-min-rem') * rem,
    sizeMax: num('size-max-rem') * rem,
    alpha: num('alpha'),
    drift: num('drift-px'),
    letters: text('letters').split(',').map((c) => c.trim()).filter(Boolean),
    font: text('font'),
  }
}

// A hex colour with an alpha, for a gradient stop.
const withAlpha = (hex, a) => {
  const n = parseInt(hex.slice(1), 16)
  return `rgba(${n >> 16}, ${(n >> 8) & 255}, ${n & 255}, ${a})`
}

export default function Backdrop() {
  const canvas = useRef(null)

  useEffect(() => {
    const node = canvas.current
    const ctx = node?.getContext('2d')
    if (!ctx) return
    const root = document.documentElement
    // --c is set on App's wrapper, the canvas's parent, not on :root.
    const wrapper = node.parentElement

    let knobs = readKnobs(getComputedStyle(root))
    let tab = knobs.colors[0]
    let w = 0
    let h = 0
    let lights = []
    let marks = []
    let marksKnobs = readMarks(getComputedStyle(root))
    let raf = 0
    let frames = 0
    let held = 0

    const scale = () => parseFloat(getComputedStyle(root).getPropertyValue('--motion-scale'))
    const moving = () => !document.hidden && !reduced() && scale() > 0
    const readTab = () => getComputedStyle(wrapper).getPropertyValue('--c').trim() || tab

    function paint() {
      ctx.globalCompositeOperation = 'source-over'
      const ground = ctx.createLinearGradient(0, 0, 0, h)
      ground.addColorStop(0, knobs.groundTop)
      ground.addColorStop(1, knobs.groundBottom)
      ctx.fillStyle = ground
      ctx.fillRect(0, 0, w, h)
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      marks.forEach((m) => {
        ctx.font = `${m.size}px ${marksKnobs.font}`
        ctx.fillStyle = withAlpha(tab, m.alpha)
        ctx.fillText(m.letter, m.x, m.y)
      })
      ctx.globalCompositeOperation = 'lighter'
      lights.forEach((l, i) => {
        const colour = pickColor(i, knobs, tab)
        const g = ctx.createRadialGradient(l.x, l.y, 0, l.x, l.y, l.r)
        g.addColorStop(0, withAlpha(colour, knobs.alpha))
        g.addColorStop(0.6, withAlpha(colour, knobs.alpha * 0.4))
        g.addColorStop(1, withAlpha(colour, 0))
        ctx.fillStyle = g
        ctx.beginPath()
        ctx.arc(l.x, l.y, l.r, 0, Math.PI * 2)
        ctx.fill()
      })
    }

    const resize = () => {
      const dpr = window.devicePixelRatio || 1
      w = window.innerWidth
      h = window.innerHeight
      node.width = Math.round(w * dpr)
      node.height = Math.round(h * dpr)
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      lights = seed(knobs.count, w, h, knobs)
      marks = seedMarks(marksKnobs.count, w, h, marksKnobs)
      paint()
    }

    // Through a hold: one timer for its end, which repaints (the tint may have
    // changed meanwhile) and wakes the loop. True while one is pending.
    const waitOut = () => {
      const wait = heldFor()
      if (!wait) return false
      clearTimeout(held)
      held = setTimeout(() => { held = 0; paint(); run() }, wait)
      return true
    }

    const tick = () => {
      raf = 0
      if (!moving() || waitOut()) return
      step(lights, w, h, { ...knobs, speed: knobs.speed * scale() })
      stepMarks(marks, { ...marksKnobs, speed: knobs.speed * scale() })
      paint()
      node.dataset.frames = String(++frames)
      raf = requestAnimationFrame(tick)
    }
    const run = () => { if (!raf && moving()) raf = requestAnimationFrame(tick) }

    // A style write on :root or the wrapper is a tab change or a setting
    // change: repaint in the new tint and wake the loop if it was stopped.
    const watch = new MutationObserver(() => {
      tab = readTab()
      if (waitOut()) return
      paint()
      run()
    })
    watch.observe(root, { attributes: true, attributeFilter: ['style'] })
    watch.observe(wrapper, { attributes: true, attributeFilter: ['style'] })

    tab = readTab()
    resize()
    run()
    // The face loads on first use and canvas text never triggers that, so ask
    // for exactly these letters, then repaint; before then the marks would draw
    // in the fallback face for a frame, or not at all while the loop is stopped.
    if (marksKnobs.count > 0) {
      document.fonts.load(`1rem ${marksKnobs.font}`, marksKnobs.letters.join('')).then(paint)
    }
    window.addEventListener('resize', resize)
    document.addEventListener('visibilitychange', run)
    return () => {
      cancelAnimationFrame(raf)
      clearTimeout(held)
      watch.disconnect()
      window.removeEventListener('resize', resize)
      document.removeEventListener('visibilitychange', run)
    }
  }, [])

  return <canvas ref={canvas} className="backdrop" data-frames="0" aria-hidden="true" />
}
