// The skill's motion rules as functions of the frame number. Nothing here keeps
// state: every value is worked out again from the frame, so any frame renders alone.
import { Easing, interpolate, spring } from 'remotion'

export const FPS = 60
const clamp = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }

export const easeOut = Easing.bezier(0.22, 1, 0.36, 1)
export const easeIn = Easing.bezier(0.55, 0, 1, 0.45)
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1)
export const overshoot = Easing.bezier(0.34, 1.56, 0.64, 1)

/** 0 → 1 between two frames with an easing. */
export const ramp = (frame, from, to, easing = easeInOut) =>
  interpolate(frame, [from, to], [0, 1], { ...clamp, easing })

/** Entrance: about half a second, landing with a slight overshoot (spring, damping 14). */
export const enter = (frame, at, dur = 30) =>
  spring({ frame: frame - at, fps: FPS, durationInFrames: dur, config: { damping: 14, stiffness: 140, mass: 0.9 } })

/** Exit: 60% of an entrance, ease-in. 1 while shown, 0 once gone. */
export const exit = (frame, at, dur = 18) => 1 - ramp(frame, at, at + dur, easeIn)

/** A click: 1 → 0.96 → 1 over 8 frames. */
export const press = (frame, at) =>
  frame < at || frame > at + 8 ? 1 : 1 - 0.04 * Math.sin(((frame - at) / 8) * Math.PI)

/** The golden rule: nothing fully stops. A slow breathing drift for anything holding. */
export const drift = (frame, seed = 0, px = 4) => ({
  x: Math.sin(frame / 70 + seed * 1.7) * px,
  y: Math.cos(frame / 85 + seed * 2.3) * px,
})

export const lerp = (a, b, t) => a + (b - a) * t
export const mix = (frame, keys, values, easing = easeInOut) =>
  interpolate(frame, keys, values, { ...clamp, easing })

/** Split text into what a reader sees as letters (Arabic letters keep their harakat). */
const seg = new Intl.Segmenter('ar', { granularity: 'grapheme' })
export const graphemes = (s) => [...seg.segment(s)].map((g) => g.segment)

/** The first n graphemes of a string, for type-on. */
export const typed = (s, frame, from, to) => {
  const g = graphemes(s)
  const n = Math.round(interpolate(frame, [from, to], [0, g.length], clamp))
  return g.slice(0, n).join('')
}

/**
 * Cursor path: hops between key points on a quadratic arc (control point pushed
 * 15% of the distance sideways), eased, with a spring settle that overshoots a touch.
 * keys: [{ f, x, y, h? }] in frame order, f the frame it arrives, h how long the hop takes;
 * the cursor holds (hesitates) between arriving and the next hop.
 */
export function cursorAt(frame, keys, hop = 34) {
  let pos = { x: keys[0].x, y: keys[0].y }
  for (let i = 1; i < keys.length; i++) {
    const a = keys[i - 1]
    const b = keys[i]
    const h = b.h ?? hop
    const start = b.f - h
    if (frame < start) break
    const t = spring({ frame: frame - start, fps: FPS, durationInFrames: h, config: { damping: 16, stiffness: 120 } })
    const dx = b.x - a.x
    const dy = b.y - a.y
    const cx = (a.x + b.x) / 2 - dy * 0.15
    const cy = (a.y + b.y) / 2 + dx * 0.15
    const u = 1 - t
    pos = { x: u * u * a.x + 2 * u * t * cx + t * t * b.x, y: u * u * a.y + 2 * u * t * cy + t * t * b.y }
  }
  return pos
}
