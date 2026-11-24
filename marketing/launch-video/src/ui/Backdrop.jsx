import { AbsoluteFill, useCurrentFrame, random } from 'remotion'
import { C } from '../config'
import { Star } from './Star'

// The dark ground every app scene sits on: warm black, two slow embers of gold
// light, a faint star lattice turning, and film grain. Made in code, so it stays
// sharp at any zoom and matches the app's Ink look exactly.
// Grounds reach past the 1920 × 1080 stage, so a 9:16 or 1:1 cut has no bare bands.
const BLEED = { top: -520, bottom: -520, left: -60, right: -60, width: 'auto', height: 'auto' }

export function Backdrop({ frame: f0 = 0, tint = C.gold, lattice = true }) {
  const frame = useCurrentFrame() + f0
  const a = { x: 30 + Math.sin(frame / 160) * 10, y: 22 + Math.cos(frame / 190) * 8 }
  const b = { x: 74 + Math.cos(frame / 210) * 9, y: 78 + Math.sin(frame / 170) * 7 }
  const seed = Math.floor(frame / 2)
  return (
    <AbsoluteFill style={{ background: C.ink, ...BLEED }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse 55% 60% at ${a.x}% ${a.y}%, ${tint}38, transparent 70%),
            radial-gradient(ellipse 50% 55% at ${b.x}% ${b.y}%, ${C.ember}26, transparent 70%),
            radial-gradient(ellipse 80% 80% at 50% 50%, ${C.bg}, ${C.ink} 85%)`,
        }}
      />
      {lattice && (
        <AbsoluteFill style={{ opacity: 0.07, transform: `rotate(${frame * 0.02}deg) scale(1.4)` }}>
          <svg width="1920" height="1080" viewBox="0 0 1920 1080">
            <defs>
              <pattern id="lat" width="160" height="160" patternUnits="userSpaceOnUse">
                <g transform="translate(80 80)">
                  <Star r={56} stroke={C.goldHi} width={1.2} />
                </g>
              </pattern>
            </defs>
            <rect width="1920" height="1080" fill="url(#lat)" />
          </svg>
        </AbsoluteFill>
      )}
      <Grain seed={seed} opacity={0.07} />
      <AbsoluteFill style={{ background: 'radial-gradient(ellipse 75% 75% at 50% 50%, transparent 55%, rgba(0,0,0,0.55))' }} />
    </AbsoluteFill>
  )
}

export function Grain({ seed, opacity = 0.06, blend = 'overlay' }) {
  const s = Math.floor(random(`g${seed}`) * 1000)
  return (
    <AbsoluteFill style={{ opacity, mixBlendMode: blend, pointerEvents: 'none' }}>
      <svg width="100%" height="100%">
        <filter id={`n${s}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={s} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#n${s})`} />
      </svg>
    </AbsoluteFill>
  )
}

/** Warm paper ground for the hook and the logo, the landing page's light look. */
export function Paper({ frame }) {
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 70% 70% at 50% 45%, #f7efda, ${C.paper} 60%, #e2d2ad)`, ...BLEED }}>
      <Grain seed={Math.floor(frame / 2)} opacity={0.1} blend="multiply" />
    </AbsoluteFill>
  )
}
