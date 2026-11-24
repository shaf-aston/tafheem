// Shots 6-8: the analysis streaming out, the books switched on, the books connecting.
import { useVideoConfig } from 'remotion'
import { C, COPY, FONT, STREAM } from '../config'
import T from '../timeline.json'
import { Stage, Bleed, At, Camera, SAFE, useFit } from '../ui/Stage'
import { WarmBg, Orb, Toggle, Cursor, Pill, Pic } from '../ui/Kit'
import { enter, mix, ramp, cursorAt, easeOut, easeInOut } from '../motion'

// Shot 6. The reference scrolls code; Tafheem's "code" is its word-by-word i'rab.
export function Stream({ frame }) {
  const f = frame - 530
  const zoom = mix(f, [0, 24], [0.78, 1], easeOut)
  const scroll = mix(f, [0, 70], [260, -1500], (t) => t * t * (3 - 2 * t) * 0.6 + t * 0.4)
  const lines = [...STREAM, ...STREAM]
  return (
    <>
      <Bleed>
        <WarmBg frame={frame} seed={3} light={1.2} />
      </Bleed>
      <Stage>
        <Camera scale={zoom * useFit(1460)}>
          <div
            style={{
              position: 'absolute',
              left: 960 - 700,
              top: 540 + scroll,
              fontFamily: FONT.mono,
              fontSize: 40,
              lineHeight: '60px',
              color: C.text,
              whiteSpace: 'pre',
            }}
          >
            {lines.map((l, i) => (
              <div key={i} style={{ height: 60, opacity: l[0].includes('"') ? 1 : 0.6 }}>
                {l[0]}
                {l[2] != null && (
                  <>
                    <span style={{ fontFamily: FONT.arabic, color: C.saffronHi, fontSize: 40, unicodeBidi: 'isolate', direction: 'rtl' }}>{l[1]}</span>
                    {l[2]}
                  </>
                )}
              </div>
            ))}
          </div>
        </Camera>
      </Stage>
    </>
  )
}

// Shot 7. "Connect the classical books" and a switch the cursor flips.
export function Connect({ frame }) {
  const f = frame - 600
  const click = T.cue.toggleClick
  const on = ramp(frame, click, click + 10, easeOut)
  const s = mix(f, [0, 75], [0.96, 1.06], easeInOut) * useFit(1560)
  const c = cursorAt(frame, [
    { f: 600, x: 640, y: 360 },
    { f: click - 4, x: 600, y: 18, h: 30 },
  ])
  return (
    <>
      <Bleed>
        <WarmBg frame={frame} seed={3.6} />
      </Bleed>
      <Stage>
        <Camera scale={s} x={f * 0.4}>
          <At x={0}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 34 }}>
              <Orb frame={frame} size={110} />
              <span style={{ fontFamily: FONT.ui, fontSize: 86, letterSpacing: -3, fontWeight: 500, color: C.text, whiteSpace: 'nowrap' }}>{COPY.connect}</span>
              <Toggle on={on} scale={1.9} />
            </div>
          </At>
          <Cursor x={c.x} y={c.y} frame={frame} clicks={[click]} size={1.3} />
        </Camera>
      </Stage>
    </>
  )
}

// A small seeded random, so the tile field is the same on every render.
function rng(seed) {
  let a = seed
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const SWATCH = [C.saffron, '#e2491c', C.peach, C.lavender, C.navy, '#f0ebe8', '#f6a45a']
const LETTERS = ['ك', 'ت', 'ب', 'ق', 'ر', 'أ', 'ع', 'ل', 'م']
const IMGS = [
  ['folio.jpg', 2.4, 40, 50, 'multiply'],
  ['quran.jpg', 3, 66, 92, 'screen'],
  ['folio.jpg', 3, 80, 30, 'multiply'],
  ['sarf.jpg', 3.4, 30, 40, 'screen'],
  ['folio.jpg', 2.8, 20, 80, 'multiply'],
  ['nahw.jpg', 2.4, 100, 23, 'screen'],
]
const LIGHT = new Set([C.peach, '#f0ebe8', '#f6a45a', C.lavender])

const R = rng(96)
const TILES = Array.from({ length: 44 }, (_, i) => {
  const kind = i % 5 === 0 ? 'img' : i % 7 === 3 ? 'letter' : 'color'
  return {
    x: -0.05 + R() * 1.1,
    y: -0.05 + R() * 1.1,
    size: 90 + R() * 130,
    depth: 0.55 + R() * 0.9,
    color: SWATCH[Math.floor(R() * SWATCH.length)],
    kind,
    img: IMGS[i % IMGS.length],
    letter: LETTERS[i % LETTERS.length],
  }
})
// Keep the middle clear for the pill.
TILES.forEach((t) => {
  if (Math.abs(t.x - 0.5) < 0.16 && Math.abs(t.y - 0.5) < 0.1) t.y += t.y < 0.5 ? -0.16 : 0.16
})
const LINKS = [
  [0, 7], [7, 12], [12, 3], [5, 19], [19, 25], [25, 30], [2, 14], [14, 21], [9, 33], [33, 40], [16, 28], [28, 37], [11, 23],
]

// Shot 8. Book tiles, letters and real screens float in depth while lines join them.
export function Web({ frame }) {
  const { width: W, height: H } = useVideoConfig()
  const u = Math.min(W / SAFE, H / 1080)
  const f = frame - 658
  const zoom = 1 + f * 0.0028
  const place = (t) => {
    const k = zoom ** t.depth
    const cx = W / 2 + (t.x - 0.5) * W * k + Math.sin(frame / 50 + t.depth * 9) * 6
    const cy = H / 2 + (t.y - 0.5) * H * k + Math.cos(frame / 60 + t.x * 9) * 6
    return { cx, cy, s: t.size * u * k * (0.75 + 0.25 * t.depth) }
  }
  return (
    <>
      <Bleed>
        <WarmBg frame={frame} seed={4} light={1.4} />
        <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
          {LINKS.map(([a, b], i) => {
            const p = place(TILES[a])
            const q = place(TILES[b])
            const len = Math.hypot(q.cx - p.cx, q.cy - p.cy)
            const draw = ramp(frame, 667 + i * 3, 687 + i * 3, easeOut)
            return (
              <line
                key={i}
                x1={p.cx}
                y1={p.cy}
                x2={q.cx}
                y2={q.cy}
                stroke="rgba(255,240,230,0.7)"
                strokeWidth={1.6 * u}
                strokeDasharray={len}
                strokeDashoffset={len * (1 - draw)}
              />
            )
          })}
        </svg>
        {TILES.map((t, i) => {
          const { cx, cy, s } = place(t)
          const dist = Math.hypot(t.x - 0.5, t.y - 0.5)
          const pop = enter(frame, 658 + dist * 30, 22)
          const blur = Math.max(0, Math.abs(t.depth - 1.05) - 0.18) * 14
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: cx - s / 2,
                top: cy - s / 2,
                width: s,
                height: s,
                transform: `scale(${pop})`,
                filter: blur > 0.5 ? `blur(${blur}px)` : undefined,
                background: t.color,
                boxShadow: t.kind === 'img' ? '0 0 0 2px rgba(255,255,255,0.75)' : undefined,
                overflow: 'hidden',
                display: 'grid',
                placeItems: 'center',
                color: LIGHT.has(t.color) ? '#5a2c10' : '#fff',
                fontFamily: FONT.arabic,
                fontSize: s * 0.5,
                lineHeight: 1,
              }}
            >
              {t.kind === 'img' && (
                <>
                  <Pic src={t.img[0]} w={s} h={s} zoom={t.img[1]} ox={t.img[2]} oy={t.img[3]} />
                  <div style={{ position: 'absolute', inset: 0, background: t.color, mixBlendMode: t.img[4], opacity: t.img[4] === 'screen' ? 0.55 : 0.85 }} />
                </>
              )}
              {t.kind === 'letter' && <span style={{ paddingBottom: s * 0.1 }}>{t.letter}</span>}
            </div>
          )
        })}
      </Bleed>
      <Stage>
        <At>
          <div style={{ transform: `scale(${0.85 + 0.15 * enter(frame, 663, 24)})` }}>
            <Pill frame={frame} text={COPY.connecting} />
          </div>
        </At>
      </Stage>
    </>
  )
}
