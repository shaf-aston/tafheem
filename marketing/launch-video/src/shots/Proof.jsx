// Shots 12-14: counting dots, the folio with the ayah counter, the dashboard.
import { AbsoluteFill, Img, staticFile, useVideoConfig } from 'remotion'
import { C, CARDS, COPY, COUNT_TO, DASH, FONT, LESSONS } from '../config'
import T from '../timeline.json'
import { Stage, Bleed, At, Camera, SAFE } from '../ui/Stage'
import { WarmBg, Pill, ToolCard, Badge } from '../ui/Kit'
import { enter, mix, ramp, easeOut, easeInOut } from '../motion'

const HATCH = 'repeating-linear-gradient(135deg, rgba(0,0,0,0.28) 0 2px, transparent 2px 5px)'

// Each row: colour, direction, which part of the row holds dots (0..1 of the width).
const ROWS = [
  ['#f2a36b', 1, 0, 0.58],
  ['#e2491c', -1, 0.42, 1.1],
  ['#6d74c9', 1, -0.1, 0.58],
  ['#f2a36b', -1, 0.62, 0.8],
  ['#6d74c9', 1, 0.08, 0.58],
  ['#4b4f9a', -1, 0.42, 1.1],
  ['#f2a36b', 1, -0.1, 0.58],
  ['#e2491c', -1, 0.3, 1.1],
]

// Shot 12. Rows of halftone dots slide past while Tafheem counts.
export function Dots({ frame }) {
  const { width: W, height: H } = useVideoConfig()
  const f = frame - 930
  const pitch = H / 7.2
  const d = pitch * 0.66
  const step = d * 1.45
  return (
    <>
      <Bleed>
        <AbsoluteFill style={{ background: 'linear-gradient(100deg, #050302 0%, #160803 38%, #7a2509 75%, #c4430f 100%)' }} />
        {ROWS.map(([color, dir, a, b], r) => {
          const shift = dir * f * (3.2 + (r % 3)) * (H / 1080)
          const y = pitch * (r + 0.35)
          const dots = []
          for (let x = -2 * step; x < W + 2 * step; x += step) {
            const px = x + (((shift % step) + step) % step)
            const frac = px / W
            if (frac < a + (dir > 0 ? f * 0.003 : 0) || frac > b + (dir < 0 ? 0 : f * 0.003)) continue
            dots.push(
              <div
                key={x}
                style={{ position: 'absolute', left: px - d / 2, top: y - d / 2, width: d, height: d, borderRadius: '50%', background: color }}
              />,
            )
          }
          return <div key={r}>{dots}</div>
        })}
        <AbsoluteFill style={{ background: HATCH, opacity: 0.7 }} />
      </Bleed>
      <Stage>
        <At y={30}>
          <div style={{ transform: `scale(${0.85 + 0.15 * enter(frame, 934, 22)})` }}>
            <Pill frame={frame} text={COPY.counting} light scale={1.3} />
          </div>
        </At>
      </Stage>
    </>
  )
}

// Shot 13. The reference's real photo with a counter; ours is a real Qur'an folio.
export function Folio({ frame }) {
  const f = frame - 1000
  const n = Math.round(ramp(frame, T.cue.countFrom, T.cue.countTo, easeOut) * COUNT_TO)
  const box = enter(frame, 1004, 24)
  return (
    <>
      <Bleed>
        <AbsoluteFill style={{ transform: `scale(${1.12 + f * 0.0015})` }}>
          <Img src={staticFile('img/folio.jpg')} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </AbsoluteFill>
        <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 50% 50%, rgba(40,14,4,0.1), rgba(40,14,4,0.55))' }} />
      </Bleed>
      <Stage>
        <At y={-20}>
          <div
            style={{
              transform: `scale(${0.9 + 0.1 * box})`,
              opacity: box,
              padding: '26px 64px 34px',
              borderRadius: 18,
              background: 'linear-gradient(135deg, rgba(244,145,59,0.82), rgba(214,70,26,0.62))',
              backdropFilter: 'blur(14px)',
              boxShadow: '0 30px 90px rgba(0,0,0,0.45), inset 0 0 0 1.5px rgba(255,220,190,0.45)',
              textAlign: 'center',
              color: '#fff',
              fontFamily: FONT.ui,
              minWidth: 620,
            }}
          >
            <div style={{ fontSize: 190, fontWeight: 600, letterSpacing: -8, lineHeight: 1, fontVariantNumeric: 'tabular-nums' }}>{n.toLocaleString('en-US')}</div>
            <div style={{ fontSize: 44, letterSpacing: -1, marginTop: 8 }}>{COPY.countLabel}</div>
          </div>
        </At>
      </Stage>
    </>
  )
}

function Panel({ children, style }) {
  return (
    <div
      style={{
        position: 'absolute',
        background: 'linear-gradient(160deg, rgba(30,24,22,0.92), rgba(14,11,10,0.92))',
        border: `1px solid ${C.line}`,
        borderRadius: 16,
        boxShadow: '0 24px 70px rgba(0,0,0,0.45)',
        color: C.text,
        fontFamily: FONT.ui,
        boxSizing: 'border-box',
        ...style,
      }}
    >
      {children}
    </div>
  )
}

const Check = () => (
  <div style={{ width: 24, height: 24, borderRadius: '50%', background: C.saffron, display: 'grid', placeItems: 'center', flex: 'none' }}>
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2a1408" strokeWidth="3.4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12.5l4.5 4.5L19 7.5" />
    </svg>
  </div>
)

// Shot 14. The dashboard builds piece by piece, as in the reference.
export function Dash({ frame }) {
  const f = frame - 1060
  const at = T.cue.dashIn
  const show = (t0, dy = 40) => {
    const t = enter(frame, t0, 26)
    return { opacity: Math.min(1, t * 1.6), transform: `translateY(${(1 - t) * dy}px)` }
  }
  const streak = Math.round(ramp(frame, at + 64, at + 104, easeOut) * DASH.streak)
  const slot = frame < at + 90 ? 1 : 1 + ramp(frame, at + 90, at + 100)
  const L = 960 - 640
  const TOP = 540 - 330
  return (
    <>
      <Bleed>
        <WarmBg frame={frame} seed={7} />
      </Bleed>
      <Stage>
        <Camera scale={mix(f, [0, 170], [0.95, 1.05], easeInOut)} x={mix(f, [0, 170], [-30, 20], easeInOut)}>
          <div style={{ position: 'absolute', left: L, top: TOP - 110, fontFamily: FONT.ui, fontSize: 66, letterSpacing: -2.4, fontWeight: 500, color: C.text, ...show(at, 20) }}>
            {COPY.dash}
          </div>
          {/* sidebar */}
          <Panel style={{ left: L, top: TOP, width: 68, height: 700, borderRadius: 34, background: 'rgba(120,70,50,0.35)', ...show(at + 70, 0) }}>
            {[0, 1, 2, 3, 4].map((i) => (
              <div key={i} style={{ position: 'absolute', left: 24, top: 40 + i * 62, width: 20, height: 20, borderRadius: '50%', background: 'rgba(255,255,255,0.45)' }} />
            ))}
            <div style={{ position: 'absolute', left: 16, top: 40 + slot * 62 - 8, width: 36, height: 36, borderRadius: '50%', background: C.saffron }} />
            <div style={{ position: 'absolute', left: 24, top: 650, width: 20, height: 20, borderRadius: '50%', background: 'rgba(255,255,255,0.45)' }} />
          </Panel>
          {/* top row: the three tools */}
          {CARDS.map((card, i) => (
            <div key={i} style={{ position: 'absolute', left: L + 92 + i * 392, top: TOP, ...show(at + i * 10) }}>
              <ToolCard card={card} on={1} w={440} k={0.86} />
            </div>
          ))}
          {/* latest lessons */}
          <Panel style={{ left: L + 92, top: TOP + 278, width: 420, height: 422, padding: '26px 26px', ...show(at + 30) }}>
            <div style={{ fontSize: 28, letterSpacing: -0.6, marginBottom: 18 }}>Latest lessons</div>
            {LESSONS.map(([text, when], i) => (
              <div
                key={text}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  height: 56,
                  opacity: ramp(frame, at + 36 + i * 5, at + 46 + i * 5),
                }}
              >
                <Check />
                <span style={{ fontSize: 21, flex: 1 }}>{text}</span>
                <span style={{ fontSize: 15, color: C.faint }}>{when}</span>
              </div>
            ))}
          </Panel>
          {/* words today */}
          <Panel style={{ left: L + 530, top: TOP + 278, width: 300, height: 200, padding: '22px 26px', ...show(at + 42) }}>
            <div style={{ fontSize: 13, letterSpacing: 0.8, color: C.dim }}>WORDS UNDERSTOOD TODAY</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 18, marginTop: 14 }}>
              <span style={{ fontSize: 92, letterSpacing: -4, lineHeight: 1 }}>{DASH.wordsToday}</span>
              <span style={{ background: C.peach, color: '#2a1408', borderRadius: 999, padding: '4px 14px', fontSize: 21, fontWeight: 600 }}>▲ {DASH.wordsUp}</span>
            </div>
          </Panel>
          {/* tools online */}
          <Panel style={{ left: L + 530, top: TOP + 496, width: 300, height: 204, padding: '22px 26px', ...show(at + 52) }}>
            <div style={{ fontSize: 13, letterSpacing: 0.8, color: C.dim }}>TOOLS ONLINE · OFFLINE READY</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 46 }}>
              {['ن', 'ص', 'ق'].map((g) => (
                <Badge key={g} glyph={g} size={46} />
              ))}
              <span style={{ fontSize: 24, marginLeft: 10, whiteSpace: 'nowrap' }}>{DASH.tools}</span>
            </div>
          </Panel>
          {/* the big saffron card, the reference's "999" */}
          <div
            style={{
              position: 'absolute',
              left: L + 852,
              top: TOP + 330,
              width: 430,
              height: 290,
              borderRadius: 18,
              background: C.saffron,
              boxShadow: `0 0 60px rgba(244,145,59,0.5), inset 0 0 0 2px rgba(255,220,180,0.6)`,
              padding: '24px 30px',
              boxSizing: 'border-box',
              fontFamily: FONT.ui,
              color: '#2a1408',
              ...show(at + 60, 60),
              transform: `scale(${0.8 + 0.2 * enter(frame, at + 60, 26)})`,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 21 }}>
              <span>Day streak</span>
              <span style={{ background: 'rgba(255,255,255,0.4)', borderRadius: 999, padding: '3px 12px', fontSize: 15 }}>● Live</span>
            </div>
            <div style={{ fontSize: 168, fontWeight: 600, letterSpacing: -8, color: '#1f2f27', lineHeight: 1, marginTop: 8, textAlign: 'center' }}>{streak}</div>
            <div style={{ fontSize: 15, textAlign: 'right', opacity: 0.75 }}>days of reading with understanding</div>
          </div>
        </Camera>
      </Stage>
    </>
  )
}
