/**
 * The lantern backdrop's arithmetic: where each light starts, how it drifts,
 * what colour it wears. No DOM and no canvas, so it is testable with numbers
 * and Backdrop.jsx is left with nothing but drawing.
 *
 * knobs = { sizeMin, sizeMax, speed, tint, colors } (theme.json's lights
 * group, read by the component; the marks functions add letters, alpha, drift).
 * speed is pixels per frame; the component multiplies it by the Animations
 * scale, so 0 here means standing still.
 */

// A share of the lights wear the tab colour, chosen by index on a golden-ratio
// stride, so the same lights stay tinted when the tab changes and they spread
// evenly instead of clumping the way a random pick would.
const STRIDE = 0.6180339887

/** n lights with a size, a place inside w x h and a drift direction. */
export function seed(n, w, h, knobs, rand = Math.random) {
  return Array.from({ length: n }, () => {
    const angle = rand() * Math.PI * 2
    const pace = 0.5 + rand()
    return {
      x: rand() * w,
      y: rand() * h,
      r: knobs.sizeMin + rand() * (knobs.sizeMax - knobs.sizeMin),
      dx: Math.cos(angle) * pace,
      dy: Math.sin(angle) * pace,
    }
  })
}

/** Move every light one frame; one that has fully left an edge re-enters opposite. */
export function step(lights, w, h, knobs) {
  for (const l of lights) {
    l.x += l.dx * knobs.speed
    l.y += l.dy * knobs.speed
    if (l.x - l.r > w) l.x = -l.r
    else if (l.x + l.r < 0) l.x = w + l.r
    if (l.y - l.r > h) l.y = -l.r
    else if (l.y + l.r < 0) l.y = h + l.r
  }
  return lights
}

/** Light i's colour: the tab's, for the tinted share, else one of the warm lights. */
export function pickColor(i, knobs, tabColor) {
  if (((i * STRIDE) % 1) < knobs.tint) return tabColor
  return knobs.colors[i % knobs.colors.length]
}

// Marks: big faint letters. Each sits at a home point and wanders a small
// ellipse round it, so a letter never leaves the page the way a light does and
// the layout stays stable. One lap takes about TAU / (speed * LAP) frames.
const LAP = 0.02

/** n marks: a letter, a size in px, a home inside w x h, a fixed alpha, a drift phase and pace. */
export function seedMarks(n, w, h, knobs, rand = Math.random) {
  return Array.from({ length: n }, () => {
    const home = { hx: rand() * w, hy: rand() * h }
    return {
      ...home,
      x: home.hx,
      y: home.hy,
      size: knobs.sizeMin + rand() * (knobs.sizeMax - knobs.sizeMin),
      letter: knobs.letters[Math.floor(rand() * knobs.letters.length)],
      alpha: knobs.alpha,
      phase: rand() * Math.PI * 2,
      pace: 0.5 + rand(),
    }
  })
}

/** Move every mark one frame along its ellipse; drift 0 holds it at home. */
export function stepMarks(marks, knobs) {
  for (const m of marks) {
    m.phase += knobs.speed * m.pace * LAP
    m.x = m.hx + Math.cos(m.phase) * knobs.drift
    m.y = m.hy + Math.sin(m.phase * 0.7) * knobs.drift
  }
  return marks
}
