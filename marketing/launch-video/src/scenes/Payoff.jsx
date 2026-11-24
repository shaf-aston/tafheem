import { AbsoluteFill, interpolate } from 'remotion'
import T from '../timeline.json'
import { C, COPY, COUNT_TO, FONT, TODAY, TOOLS } from '../config'
import { enter, exit, mix, ramp, typed, drift, cursorAt, easeOut, easeIn } from '../motion'
import { Stage, At, Camera } from '../ui/Stage'
import { Backdrop, Paper } from '../ui/Backdrop'
import { Check, Cursor, Eyebrow, Glass } from '../ui/Parts'
import { PromptBar } from '../ui/PromptBar'
import { Mark } from '../ui/Mark'
import { Star } from '../ui/Star'

const P = T.payoff
const END = T.scenes.payoff[1]

// Scene 4 · Payoff: the size of what is checked (a count-up), the study
// dashboard resolving as the camera pulls back, the opening question answered
// in the bar, then the logo on paper.
export function Payoff({ frame }) {
  const irisR = mix(frame, [P.logoFrom - 8, P.logoFrom + 16], [0, 2400], easeIn)
  return (
    <AbsoluteFill>
      <Stage>
        <Backdrop />
        {frame < P.dashFrom + 10 && <Count frame={frame} />}
        {frame >= P.dashFrom - 6 && frame < P.logoFrom + 16 && <Dashboard frame={frame} />}
        {frame >= P.logoFrom - 8 && (
          <AbsoluteFill style={{ clipPath: `circle(${irisR}px at ${960 + 450}px ${540 + 352}px)` }}>
            <Logo frame={frame} />
          </AbsoluteFill>
        )}
      </Stage>
    </AbsoluteFill>
  )
}

function Count({ frame }) {
  const inn = ramp(frame, 1230, 1246, easeOut)
  const out = exit(frame, P.dashFrom - 8, 16)
  const n = Math.round(interpolate(frame, [P.countFrom, P.countTo], [0, COUNT_TO], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: easeOut }))
  const chip = enter(frame, 1234)
  const chipOut = exit(frame, P.countFrom - 6, 12)
  const big = enter(frame, P.countFrom - 4, 30)
  const label = enter(frame, P.countFrom + 20)
  const sub = enter(frame, P.countTo + 10)
  return (
    <Camera frame={frame - 1230} scale={1 + 0.04 * ramp(frame, 1230, P.dashFrom)} push={0}>
      <AbsoluteFill style={{ opacity: inn * out }}>
        <DotField frame={frame} />
        <At y={-10}>
          <div style={{ opacity: Math.min(1, chip) * chipOut, transform: `scale(${chip})`, display: 'flex', alignItems: 'center', gap: 14, padding: '16px 30px', borderRadius: 18, background: C.text, color: C.bg, fontFamily: FONT.ui, fontSize: 30, fontWeight: 500 }}>
            <svg width="26" height="26" viewBox="0 0 26 26" style={{ transform: `rotate(${frame * 8}deg)` }}><circle cx="13" cy="13" r="10" fill="none" stroke={C.bg} strokeWidth="3" strokeDasharray="40 30" strokeLinecap="round" /></svg>
            Opening the corpus
          </div>
        </At>
        <At y={-50}>
          <div style={{ fontFamily: FONT.head, fontSize: 280, fontWeight: 700, color: C.text, lineHeight: 1, letterSpacing: '-0.04em', opacity: frame >= P.countFrom - 4 ? Math.min(1, big) : 0, transform: `scale(${0.85 + 0.15 * big})`, textShadow: `0 20px 80px ${C.gold}55`, fontVariantNumeric: 'tabular-nums' }}>
            {n.toLocaleString('en-US')}
          </div>
        </At>
        <At y={120}>
          <div style={{ fontFamily: FONT.head, fontStyle: 'italic', fontSize: 48, color: C.goldHi, opacity: Math.min(1, label), transform: `translateY(${(1 - label) * 20}px)`, whiteSpace: 'nowrap' }}>{COPY.countLabel}</div>
        </At>
        <At y={210}>
          <div style={{ fontFamily: FONT.label, fontSize: 18, letterSpacing: '0.1em', textTransform: 'uppercase', color: C.dim, opacity: Math.min(1, sub), transform: `translateY(${(1 - sub) * 16}px)`, whiteSpace: 'nowrap' }}>{COPY.countSub}</div>
        </At>
      </AbsoluteFill>
    </Camera>
  )
}

// A wall of dots, rows sliding opposite ways, a wave of gold running through.
function DotField({ frame }) {
  const rows = 9
  const cols = 22
  return (
    <AbsoluteFill style={{ opacity: 0.85 }}>
      {[...Array(rows)].map((_, r) => (
        <div key={r} style={{ position: 'absolute', top: 60 + r * 118, left: -200 + ((frame * (r % 2 ? 0.6 : -0.6)) % 112), display: 'flex', gap: 62 }}>
          {[...Array(cols)].map((__, c) => {
            const wave = Math.sin(c * 0.45 - r * 0.35 + frame / 14)
            const hot = wave > 0.55
            const col = hot ? C.gold : r % 3 === 0 ? '#3b3561' : '#3a2a1c'
            return <div key={c} style={{ width: 50, height: 50, borderRadius: '50%', background: col, opacity: hot ? 0.75 : 0.5, boxShadow: hot ? `0 0 26px ${C.gold}88` : 'none' }} />
          })}
        </div>
      ))}
      <AbsoluteFill style={{ background: 'radial-gradient(ellipse 45% 40% at 50% 48%, rgba(15,13,11,0.92), rgba(15,13,11,0.35) 75%, transparent)' }} />
    </AbsoluteFill>
  )
}

function Dashboard({ frame }) {
  const f0 = P.dashFrom
  const inn = ramp(frame, f0 - 6, f0 + 10)
  const pull = mix(frame, [f0, f0 + 80], [1.22, 1.0], easeOut)
  const closeUp = mix(frame, [P.typeFrom - 20, P.send + 4, P.logoFrom], [0, 1, 1.3])
  const scale = pull + 0.08 * closeUp
  const camX = 0
  const camY = 352 * closeUp * 0.5
  const title = enter(frame, f0 + 4)
  const bar = enter(frame, P.typeFrom - 30, 30)
  const text = typed(COPY.closing, frame, P.typeFrom, P.typeTo)
  const cur = cursorAt(frame, [
    { f: P.typeTo - 10, x: 120, y: 520 },
    { f: P.send - 12, x: 420, y: 388, h: 30 },
    { f: P.send - 2, x: 448, y: 362, h: 10 },
  ])
  const words = Math.round(interpolate(frame, [f0 + 110, f0 + 170], [0, 48], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: easeOut }))
  const tile = enter(frame, f0 + 104, 30)
  const level = ramp(frame, f0 + 80, f0 + 150, easeOut)
  return (
    <Camera frame={frame - f0} scale={scale} x={camX} y={camY} push={0}>
      <AbsoluteFill style={{ opacity: inn }}>
        <div style={{ position: 'absolute', left: 960 - 520, top: 540 - 420, opacity: Math.min(1, title), transform: `translateY(${(1 - title) * 20}px)` }}>
          <Eyebrow>Tafheem</Eyebrow>
          <div style={{ fontFamily: FONT.head, fontSize: 64, fontWeight: 600, color: C.text, marginTop: 4 }}>{COPY.dashTitle}</div>
        </div>
        {TOOLS.map(([name, ar, note, tone], i) => {
          const e = enter(frame, f0 + 10 + i * 6, 30)
          const d = drift(frame, i, 1.5)
          const col = i % 4
          const row = Math.floor(i / 4)
          return (
            <div key={name} style={{ position: 'absolute', left: 960 - 520 + col * 164 + d.x, top: 540 - 248 + row * 164 + (1 - e) * 50 + d.y, opacity: Math.min(1, e * 1.3), transform: `scale(${0.85 + 0.15 * e})` }}>
              <Glass style={{ width: 150, height: 150, padding: 18, boxSizing: 'border-box', borderRadius: 20, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div style={{ fontFamily: FONT.arabic, fontSize: 32, color: tone, direction: 'rtl', textAlign: 'right', lineHeight: 1.2 }}>{ar}</div>
                <div>
                  <div style={{ fontSize: 22, fontWeight: 600 }}>{name}</div>
                  <div style={{ fontSize: 14, color: C.faint }}>{note}</div>
                </div>
              </Glass>
            </div>
          )
        })}
        <div style={{ position: 'absolute', left: 960 - 520, top: 540 + 88, opacity: Math.min(1, enter(frame, f0 + 64)) }}>
          <Glass style={{ width: 642, height: 120, padding: '20px 26px', boxSizing: 'border-box', borderRadius: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 20 }}>
              <span style={{ fontWeight: 600 }}>Level 4 · Reader</span>
              <span style={{ color: C.goldHi, fontVariantNumeric: 'tabular-nums' }}>{Math.round(level * 72)}%</span>
            </div>
            <div style={{ marginTop: 18, height: 14, borderRadius: 7, background: 'rgba(255,255,255,0.07)' }}>
              <div style={{ height: '100%', width: `${level * 72}%`, borderRadius: 7, background: `linear-gradient(90deg, ${C.gold}, ${C.goldHi})`, boxShadow: `0 0 18px ${C.gold}88` }} />
            </div>
          </Glass>
        </div>
        <div style={{ position: 'absolute', left: 960 + 142, top: 540 - 248, opacity: Math.min(1, enter(frame, f0 + 30)) }}>
          <Glass style={{ width: 378, padding: '18px 22px', boxSizing: 'border-box', borderRadius: 20 }}>
            <div style={{ fontSize: 18, color: C.dim, marginBottom: 8 }}>Today</div>
            {TODAY.map(([tag, line], i) => {
              const at = f0 + 40 + i * 8
              const e = enter(frame, at, 26)
              return (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, height: 44, opacity: Math.min(1, e), transform: `translateX(${(1 - e) * 30}px)` }}>
                  <Check size={24} p={ramp(frame, at + 8, at + 20)} />
                  <span style={{ fontFamily: FONT.arabic, fontSize: 17, color: C.goldHi, width: 52 }}>{tag}</span>
                  <span style={{ fontSize: 16, color: C.text, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', width: 240, fontFamily: `${FONT.ui}, ${FONT.arabic}` }}>{line}</span>
                </div>
              )
            })}
          </Glass>
        </div>
        <div style={{ position: 'absolute', left: 960 + 142, top: 540 + 50, opacity: Math.min(1, tile), transform: `scale(${0.8 + 0.2 * tile}) translateY(${(1 - tile) * 40}px)` }}>
          <div style={{ width: 378, height: 158, borderRadius: 22, padding: '18px 24px', boxSizing: 'border-box', background: `linear-gradient(140deg, ${C.goldHi}, ${C.gold} 60%, #a8822f)`, color: C.bg, boxShadow: `0 24px 60px ${C.gold}44`, fontFamily: FONT.ui }}>
            <div style={{ fontSize: 18, fontWeight: 600, opacity: 0.8 }}>Words understood today</div>
            <div style={{ fontFamily: FONT.head, fontSize: 92, fontWeight: 700, lineHeight: 1.05, fontVariantNumeric: 'tabular-nums' }}>{words}</div>
          </div>
        </div>
        <At y={352}>
          <div style={{ opacity: Math.min(1, bar), transform: `translateY(${(1 - bar) * 60}px)` }}>
            <PromptBar frame={frame} text={text} placeholder="Ask anything…" button="Send" pressAt={P.send} rtl={false} width={1040} glow={ramp(frame, P.typeFrom, P.typeFrom + 16)} />
          </div>
        </At>
        {frame >= P.typeTo - 10 && <Cursor frame={frame} x={cur.x} y={cur.y} clicks={[P.send]} opacity={ramp(frame, P.typeTo - 10, P.typeTo)} />}
      </AbsoluteFill>
    </Camera>
  )
}

function Logo({ frame }) {
  const f0 = P.logoFrom
  const mark = enter(frame, f0 + 2, 36)
  const name = enter(frame, f0 + 26, 34)
  const ar = enter(frame, f0 + 38)
  const cta = enter(frame, f0 + 64, 30)
  const tag = COPY.tagline.split(' ')
  return (
    <Camera frame={frame - f0} scale={1.02} push={0.0003}>
      <Paper frame={frame} />
      <At y={-30}>
        <svg width="1300" height="1300" viewBox="-650 -650 1300 1300" style={{ transform: `rotate(${frame * -0.05}deg)` }}>
          {[560, 420].map((r, i) => (
            <Star key={r} r={r} stroke={C.paperGold} width={1.4} opacity={0.18} dash={4 * r} offset={4 * r * (1 - ramp(frame, f0 + i * 6, f0 + 60 + i * 6, easeOut))} />
          ))}
        </svg>
      </At>
      <At y={-190}>
        <div style={{ transform: `scale(${mark})`, filter: `drop-shadow(0 16px 30px rgba(119,90,21,0.35))` }}>
          <Mark size={190} line={C.paperText} gold={C.gold} draw={ramp(frame, f0, f0 + 34)} fill={ramp(frame, f0 + 18, f0 + 44)} />
        </div>
      </At>
      <At y={-8}>
        <div style={{ fontFamily: FONT.head, fontSize: 150, fontWeight: 600, color: C.paperText, letterSpacing: '-0.02em', opacity: Math.min(1, name), transform: `translateY(${(1 - name) * 40}px)`, lineHeight: 1 }}>{COPY.name}</div>
      </At>
      <At y={98}>
        <div style={{ fontFamily: FONT.arabic, fontSize: 56, color: C.paperGold, opacity: Math.min(1, ar), transform: `translateY(${(1 - ar) * 16}px)` }}>{COPY.nameAr}</div>
      </At>
      <At y={196}>
        <div style={{ fontFamily: FONT.head, fontStyle: 'italic', fontSize: 46, color: C.paperText, whiteSpace: 'nowrap' }}>
          {tag.map((w, i) => {
            const e = enter(frame, f0 + 46 + i * 4, 26)
            return <span key={i} style={{ display: 'inline-block', margin: '0 0.14em', opacity: Math.min(1, e), transform: `translateY(${(1 - e) * 24}px)` }}>{w}</span>
          })}
        </div>
      </At>
      <At y={300}>
        <div style={{ opacity: Math.min(1, cta), transform: `scale(${0.85 + 0.15 * cta})`, padding: '18px 40px', borderRadius: 999, background: C.paperText, color: C.paper, fontFamily: FONT.ui, fontSize: 30, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 14, boxShadow: '0 18px 40px rgba(36,28,17,0.3)' }}>
          {COPY.cta}
          <svg width="26" height="26" viewBox="0 0 24 24"><path d="M5 12h13M13 6l6 6-6 6" fill="none" stroke={C.goldHi} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </div>
      </At>
      <At y={380}>
        <div style={{ fontFamily: FONT.label, fontSize: 18, letterSpacing: '0.18em', textTransform: 'uppercase', color: C.paperMuted, opacity: Math.min(1, enter(frame, f0 + 76)) }}>{COPY.ctaNote}</div>
      </At>
    </Camera>
  )
}
