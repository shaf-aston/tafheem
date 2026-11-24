import { AbsoluteFill } from 'remotion'
import T from '../timeline.json'
import { AYAH, BOOKS, BRACKETS, C, COPY, FONT, ROOT_LETTERS, ROOT_WORDS, WORDS } from '../config'
import { enter, exit, mix, ramp, drift, cursorAt, easeOut, easeIn, easeInOut } from '../motion'
import { Stage, At, Camera } from '../ui/Stage'
import { Backdrop } from '../ui/Backdrop'
import { Check, Cursor, Eyebrow, Glass, Toggle } from '../ui/Parts'
import { PromptBar } from '../ui/PromptBar'
import { Star } from '../ui/Star'
import { SENTENCE } from './Problem'

const D = T.demo
const PITCH = 132
const CARD_W = 124
const CARD_Y = -130
// Word 0 is read first, so it sits on the right.
const wordX = (i) => (3.5 - i) * PITCH

// Scene 3 · Feature demo, in three beats on one camera:
// the sentence read word by word into roles and joins; the verb's root opened into
// the words it grows and the four dictionaries; then reciting, checked word by word.
export function Demo({ frame }) {
  // Beat changes: push into كَتَبَ, then pull out of the root view.
  const toRoot = ramp(frame, D.rootFrom, D.rootFrom + 30, easeIn)
  const iraabCam = { scale: 1 + toRoot * 1.6, x: wordX(3) * toRoot, y: CARD_Y * toRoot }
  return (
    <AbsoluteFill>
      <Stage>
        <Backdrop />
        {frame < D.rootFrom + 32 && (
          <Camera frame={frame - 630} {...iraabCam}>
            <AbsoluteFill style={{ opacity: 1 - ramp(frame, D.rootFrom + 14, D.rootFrom + 30) }}>
              <Iraab frame={frame} />
            </AbsoluteFill>
          </Camera>
        )}
        {frame >= D.rootFrom + 14 && frame < D.reciteFrom + 22 && <Root frame={frame} />}
        {frame >= D.reciteFrom && <Recite frame={frame} />}
      </Stage>
    </AbsoluteFill>
  )
}

function Iraab({ frame }) {
  const barY = mix(frame, [630, 664], [0, -330])
  const barS = mix(frame, [630, 664], [1, 0.78])
  const barOut = exit(frame, 700, 18)
  const title = enter(frame, 708)
  const meaning = enter(frame, D.brackets + 70)
  const note = enter(frame, D.governor + 20)
  return (
    <>
      <At y={barY}>
        <div style={{ transform: `scale(${barS * (0.9 + 0.1 * barOut)})`, opacity: barOut }}>
          <PromptBar frame={frame} text={SENTENCE} button={COPY.analyse} busy={1 - ramp(frame, 632, 650)} />
        </div>
      </At>
      <At y={-372}>
        <div style={{ opacity: title, transform: `translateY(${(1 - title) * 24}px)`, fontFamily: FONT.head, fontSize: 58, fontWeight: 600, color: C.text, whiteSpace: 'nowrap' }}>
          {COPY.demoTitle}
        </div>
      </At>
      {WORDS.map((w, i) => (
        <WordCard key={i} w={w} i={i} frame={frame} />
      ))}
      <Governor frame={frame} />
      {BRACKETS.map((b, i) => (
        <Bracket key={i} b={b} frame={frame} at={D.brackets + i * 14} />
      ))}
      <At y={300}>
        <div style={{ opacity: meaning, fontFamily: FONT.head, fontStyle: 'italic', fontSize: 30, color: C.dim, whiteSpace: 'nowrap', transform: `translateY(${(1 - meaning) * 14}px)` }}>
          “{COPY.meaning}”
        </div>
      </At>
      <At y={372}>
        <div style={{ opacity: note, transform: `scale(${0.9 + 0.1 * note})`, display: 'flex', alignItems: 'center', gap: 14, padding: '12px 26px', borderRadius: 999, border: `1.5px solid ${C.gold}66`, background: 'rgba(201,162,75,0.1)', fontFamily: FONT.ui, fontSize: 24, color: C.goldHi, whiteSpace: 'nowrap' }}>
          <Check size={26} p={ramp(frame, D.governor + 26, D.governor + 40)} />
          {COPY.demoNote}
        </div>
      </At>
    </>
  )
}

function WordCard({ w, i, frame }) {
  const at = D.cards + i * 6
  const e = enter(frame, at, 30)
  const role = ramp(frame, at + 14, at + 30, easeOut)
  const d = drift(frame, i, 2)
  const lit = i === 1 ? ramp(frame, D.governor + 10, D.governor + 24) : 0
  return (
    <At x={wordX(i) + d.x} y={CARD_Y + (1 - e) * 70 + d.y}>
      <div
        style={{
          width: CARD_W,
          height: 196,
          borderRadius: 18,
          background: C.surface,
          border: `1.5px solid ${lit ? C.goldHi : w.tone + '55'}`,
          boxShadow: `0 20px 50px rgba(0,0,0,0.45), 0 0 ${30 * role}px ${w.tone}22${lit ? `, 0 0 40px ${C.gold}88` : ''}`,
          opacity: Math.min(1, e * 1.3),
          transform: `scale(${0.8 + 0.2 * e})`,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 4,
          overflow: 'hidden',
        }}
      >
        <div style={{ height: 5, width: '100%', background: w.tone, position: 'absolute', top: 0, opacity: role }} />
        <div style={{ fontFamily: FONT.arabic, fontSize: 36, color: C.text, direction: 'rtl', lineHeight: 1.5, whiteSpace: 'nowrap' }}>{w.ar}</div>
        <div style={{ fontFamily: FONT.ui, fontSize: 15, color: C.faint, marginTop: -6 }}>{w.gl}</div>
        <div style={{ marginTop: 10, opacity: role, transform: `translateY(${(1 - role) * 10}px)`, textAlign: 'center' }}>
          <div style={{ fontFamily: FONT.arabic, fontSize: 21, fontWeight: 700, color: w.tone, direction: 'rtl', whiteSpace: 'nowrap' }}>{w.role}</div>
          <div style={{ fontFamily: FONT.label, fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase', color: w.tone, opacity: 0.8, marginTop: 2 }}>{w.en}</div>
        </div>
      </div>
    </At>
  )
}

// Rows of joins under the cards: a line between the outer words with feet, its name under it.
function Bracket({ b, frame, at }) {
  const p = ramp(frame, at, at + 22, easeOut)
  const name = enter(frame, at + 10, 26)
  const x1 = wordX(b.to) - CARD_W / 2 + 8
  const x2 = wordX(b.from) + CARD_W / 2 - 8
  const y = 0 + b.row * 64
  const w = x2 - x1
  const cx = (x1 + x2) / 2
  return (
    <At x={cx} y={y + 6}>
      <svg width={w + 4} height={22} style={{ overflow: 'visible', display: 'block', margin: '0 auto' }}>
        <path d={`M2 0 V12 H${w + 2} V0`} fill="none" stroke={b.tone} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - p} />
      </svg>
      <div style={{ textAlign: 'center', fontFamily: FONT.arabic, fontSize: 22, fontWeight: 700, color: b.tone, direction: 'rtl', whiteSpace: 'nowrap', opacity: Math.min(1, name), transform: `translateY(${(1 - name) * -8}px)`, marginTop: -2 }}>{b.name}</div>
    </At>
  )
}

// إِنَّ reaches the noun it puts in the accusative.
function Governor({ frame }) {
  const p = ramp(frame, D.governor, D.governor + 24, easeInOut)
  const chip = enter(frame, D.governor + 14)
  const x0 = wordX(0)
  const x1 = wordX(1)
  const top = CARD_Y - 98
  return (
    <>
      <At x={(x0 + x1) / 2} y={top - 22}>
        <svg width={PITCH + 40} height={60} viewBox={`0 0 ${PITCH + 40} 60`} style={{ overflow: 'visible' }}>
          <path d={`M${PITCH + 20} 56 C ${PITCH + 10} 4, 30 4, 20 56`} fill="none" stroke={C.goldHi} strokeWidth="3" strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - p} />
          <circle cx={20} cy={56} r={6 * ramp(frame, D.governor + 20, D.governor + 28)} fill={C.goldHi} />
        </svg>
      </At>
      <At x={(x0 + x1) / 2 - 150} y={top - 58}>
        <div style={{ opacity: Math.min(1, chip), transform: `scale(${chip})`, whiteSpace: 'nowrap', padding: '6px 16px', borderRadius: 12, background: C.goldHi, color: C.bg, fontFamily: FONT.ui, fontWeight: 600, fontSize: 19 }}>
          <span style={{ fontFamily: FONT.arabic, fontSize: 21 }}>إِنَّ</span> puts it in the accusative
        </div>
      </At>
    </>
  )
}

function Root({ frame }) {
  const inR = ramp(frame, D.rootFrom + 14, D.rootFrom + 40, easeOut)
  const out = ramp(frame, D.reciteFrom, D.reciteFrom + 20, easeIn)
  const title = enter(frame, D.rootFrom + 22)
  const scale = (0.6 + 0.4 * inR) * (1 + 0.6 * out)
  return (
    <Camera frame={frame - D.rootFrom} scale={scale} push={0.00025}>
      <AbsoluteFill style={{ opacity: inR * (1 - out) }}>
        <At y={-400}>
          <div style={{ opacity: Math.min(1, title), transform: `translateY(${(1 - title) * 24}px)`, fontFamily: FONT.head, fontSize: 58, fontWeight: 600, color: C.text, whiteSpace: 'nowrap' }}>{COPY.rootTitle}</div>
        </At>
        <At y={-20}>
          <svg width="420" height="420" viewBox="-210 -210 420 420" style={{ transform: `rotate(${frame * 0.15}deg)` }}>
            <Star r={190} stroke={C.gold} width={1.5} opacity={0.5} />
            <Star r={150} stroke={C.goldHi} width={1} opacity={0.25} inner={0.7} />
          </svg>
        </At>
        {ROOT_WORDS.map(([ar, gl, deg], i) => {
          const a = (deg * Math.PI) / 180
          const rx = 410
          const ry = 210
          const at = D.rootWords + i * 6
          const e = enter(frame, at, 30)
          const line = ramp(frame, at - 4, at + 16, easeOut)
          const d = drift(frame, i + 3, 4)
          const x = Math.cos(a) * rx * (0.4 + 0.6 * e) + d.x
          const y = -20 - Math.sin(a) * ry * (0.4 + 0.6 * e) + d.y
          return (
            <div key={ar}>
              <svg style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible' }} width="1920" height="1080">
                <line x1={960} y1={520} x2={960 + (x * 0.82) * line} y2={520 + ((y + 20) * 0.82) * line} stroke={C.gold} strokeOpacity="0.4" strokeWidth="1.6" strokeDasharray="5 7" />
              </svg>
              <At x={x} y={y}>
                <Glass style={{ padding: '10px 26px 12px', textAlign: 'center', opacity: Math.min(1, e), transform: `scale(${0.7 + 0.3 * e})`, borderRadius: 18 }}>
                  <div style={{ fontFamily: FONT.arabic, fontSize: 42, lineHeight: 1.45, direction: 'rtl', whiteSpace: 'nowrap' }}>{ar}</div>
                  <div style={{ fontFamily: FONT.ui, fontSize: 17, color: C.dim, whiteSpace: 'nowrap' }}>{gl}</div>
                </Glass>
              </At>
            </div>
          )
        })}
        <At y={-24}>
          <div style={{ display: 'flex', direction: 'rtl', gap: 26, fontFamily: FONT.arabic, fontSize: 112, fontWeight: 700, color: C.goldHi, textShadow: `0 0 40px ${C.gold}99` }}>
            {ROOT_LETTERS.map((l, i) => {
              const e = enter(frame, D.rootFrom + 18 + i * 5)
              return <span key={l} style={{ display: 'inline-block', opacity: Math.min(1, e), transform: `translateY(${(1 - e) * 30}px) scale(${e})` }}>{l}</span>
            })}
          </div>
        </At>
        <At y={380}>
          <div style={{ display: 'flex', gap: 16 }}>
            {BOOKS.map(([name, note], i) => {
              const e = enter(frame, D.books + i * 6)
              return (
                <Glass key={name} style={{ width: 240, padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 14, opacity: Math.min(1, e), transform: `translateY(${(1 - e) * 40}px)`, borderRadius: 18 }}>
                  <Check size={30} p={ramp(frame, D.books + i * 6 + 10, D.books + i * 6 + 24)} />
                  <div>
                    <div style={{ fontSize: 22, fontWeight: 600, whiteSpace: 'nowrap' }}>{name}</div>
                    <div style={{ fontSize: 15, color: C.faint }}>{note}</div>
                  </div>
                </Glass>
              )
            })}
          </div>
        </At>
      </AbsoluteFill>
    </Camera>
  )
}

function Recite({ frame }) {
  const e = enter(frame, D.reciteFrom + 6, 34)
  const title = enter(frame, D.reciteFrom + 14)
  const on = ramp(frame, D.toggleClick, D.toggleClick + 12, easeOut)
  const rec = ramp(frame, D.micClick, D.micClick + 10)
  const out = exit(frame, T.scenes.demo[1] - 12, 12)
  const cur = cursorAt(frame, [
    { f: D.reciteFrom + 4, x: 640, y: 470 },
    { f: D.toggleClick - 14, x: 420, y: -168, h: 34 },
    { f: D.toggleClick - 2, x: 438, y: -176, h: 10 },
    { f: D.micClick - 2, x: 26, y: 214, h: 20 },
  ])
  const zoom = mix(frame, [D.reciteFrom, D.toggleClick, D.micClick + 6, T.scenes.demo[1]], [1.04, 1.1, 1.0, 1.04])
  const camX = mix(frame, [D.reciteFrom, D.toggleClick, D.micClick + 6], [0, 120, 0])
  const camY = mix(frame, [D.reciteFrom, D.toggleClick, D.micClick + 6], [0, -60, 0])
  return (
    <Camera frame={frame - D.reciteFrom} scale={zoom} x={camX} y={camY}>
      <AbsoluteFill style={{ opacity: out }}>
        <At y={-400}>
          <div style={{ opacity: Math.min(1, title), transform: `translateY(${(1 - title) * 24}px)`, fontFamily: FONT.head, fontSize: 58, fontWeight: 600, color: C.text, whiteSpace: 'nowrap' }}>{COPY.reciteTitle}</div>
        </At>
        <At y={20}>
          <Glass glow={on > 0.5 ? `${C.gold}22` : undefined} style={{ width: 1040, height: 560, opacity: Math.min(1, e), transform: `scale(${0.88 + 0.12 * e}) translateY(${(1 - e) * 60}px)`, padding: '30px 40px', boxSizing: 'border-box', position: 'relative', borderRadius: 30 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Eyebrow>Memorise · Recite</Eyebrow>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: 24, color: on > 0.5 ? C.goldHi : C.dim }}>
                {COPY.offline}
                <Toggle on={on} />
              </div>
            </div>
            <div style={{ display: 'flex', direction: 'rtl', justifyContent: 'center', gap: 34, marginTop: 50 }}>
              {AYAH.map((w, i) => {
                const at = D.checkFrom + i * 16
                const ok = ramp(frame, at, at + 10, easeOut)
                const now = frame >= at - 16 && frame < at && frame >= D.micClick + 8
                return (
                  <div key={i} style={{ textAlign: 'center', position: 'relative' }}>
                    <div style={{ position: 'absolute', top: -34, left: '50%', transform: `translateX(-50%) scale(${ok})` }}><Check size={30} color={C.teal} p={ok} /></div>
                    <div style={{ fontFamily: FONT.mushaf, fontSize: 88, lineHeight: 1.6, color: ok > 0.5 ? C.teal : now ? C.text : C.dim, textShadow: ok > 0.5 ? `0 0 24px ${C.teal}66` : 'none' }}>{w.ar}</div>
                    <div style={{ height: 4, borderRadius: 2, background: C.teal, transform: `scaleX(${ok})`, marginTop: -6 }} />
                    <div style={{ fontFamily: FONT.ui, fontSize: 18, color: C.faint, marginTop: 10, direction: 'ltr' }}>{w.gl}</div>
                  </div>
                )
              })}
            </div>
            <div style={{ position: 'absolute', left: 0, right: 0, bottom: 36, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 30 }}>
              <Wave frame={frame} rec={rec} side={-1} />
              <div style={{ width: 96, height: 96, borderRadius: '50%', background: rec ? `linear-gradient(180deg, ${C.goldHi}, ${C.gold})` : C.surfaceHi, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: rec ? `0 0 0 ${10 + 8 * Math.sin(frame / 6)}px ${C.gold}22, 0 0 40px ${C.gold}66` : 'none' }}>
                <svg width="40" height="40" viewBox="0 0 24 24"><rect x="9" y="3" width="6" height="11" rx="3" fill={rec ? C.bg : C.dim} /><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21" fill="none" stroke={rec ? C.bg : C.dim} strokeWidth="2" strokeLinecap="round" /></svg>
              </div>
              <Wave frame={frame} rec={rec} side={1} />
            </div>
          </Glass>
        </At>
        <Cursor frame={frame} x={cur.x} y={cur.y} clicks={[D.toggleClick, D.micClick]} opacity={ramp(frame, D.reciteFrom + 4, D.reciteFrom + 14) * exit(frame, D.micClick + 30, 16)} />
      </AbsoluteFill>
    </Camera>
  )
}

function Wave({ frame, rec, side }) {
  return (
    <div style={{ display: 'flex', gap: 6, alignItems: 'center', height: 70, flexDirection: side < 0 ? 'row-reverse' : 'row' }}>
      {[...Array(18)].map((_, i) => {
        const h = 8 + rec * (14 + 26 * Math.abs(Math.sin(frame / 5 + i * 0.9) * Math.cos(frame / 11 + i * 0.4))) * (1 - i / 22)
        return <div key={i} style={{ width: 6, height: h, borderRadius: 3, background: C.goldHi, opacity: 0.35 + 0.65 * rec * (1 - i / 20) }} />
      })}
    </div>
  )
}
