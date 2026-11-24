import { AbsoluteFill } from 'remotion'
import T from '../timeline.json'
import { C, COPY, FONT, PILE, WORDS } from '../config'
import { enter, exit, mix, ramp, typed, drift, cursorAt, easeIn, easeOut } from '../motion'
import { Stage, At, Camera } from '../ui/Stage'
import { Backdrop } from '../ui/Backdrop'
import { Cursor } from '../ui/Parts'
import { PromptBar } from '../ui/PromptBar'

const P = T.problem
export const SENTENCE = WORDS.map((w) => w.ar).join(' ')

// Scene 2 · Problem. What studying one sentence looks like today: a pile of
// lexicons, PDFs and tabs, and still no reason why a word ends the way it does.
// The pile is pulled into one bar; the sentence types in; the cursor clicks Analyse.
export function Problem({ frame }) {
  const suck = ramp(frame, P.suck, P.suck + 18, easeIn)
  const head = exit(frame, P.suck - 4, 14)
  const bar = enter(frame, P.bar, 30)
  const text = typed(SENTENCE, frame, P.typeFrom, P.typeTo)
  const cur = cursorAt(frame, [
    { f: P.cursorFrom, x: 700, y: 460 },
    { f: P.cursorFrom + 34, x: 330, y: 92, h: 34 },
    { f: P.click - 4, x: 400, y: 22, h: 14 },
  ])
  const zoom = mix(frame, [P.bar, P.typeTo, P.click + 6, T.scenes.problem[1]], [1, 1.08, 1.1, 1])
  const camX = mix(frame, [P.typeTo, P.click, T.scenes.problem[1]], [0, 40, 0])
  return (
    <AbsoluteFill>
      <Stage>
        <Backdrop />
        <Camera frame={frame - 330} scale={zoom} x={camX}>
          {PILE.map((w, i) => {
            const at = P.pileFrom + i * 7
            const e = enter(frame, at, 30)
            const d = drift(frame, i, 5)
            const x = w.x * (1 - suck) + d.x
            const y = (w.y - (1 - e) * 160) * (1 - suck) + d.y
            return (
              <At key={w.title} x={x} y={y}>
                <Window w={w} style={{ opacity: Math.min(e, 1) * (1 - suck), transform: `rotate(${w.r * (1 - suck) + (1 - e) * 8}deg) scale(${(0.85 + 0.15 * e) * (1 - 0.8 * suck)})` }} />
              </At>
            )
          })}
          <At y={-10}>
            <div style={{ textAlign: 'center', opacity: head, transform: `scale(${1 - 0.1 * (1 - head)})` }}>
              <Line frame={frame} at={P.headline} text={COPY.problemA} color={C.text} />
              <Line frame={frame} at={P.headline + 26} text={COPY.problemB} color={C.goldHi} italic />
            </div>
          </At>
          {frame >= P.bar && (
            <At>
              <div style={{ transform: `scale(${bar})`, opacity: Math.min(1, bar * 1.4) }}>
                <PromptBar frame={frame} text={text} placeholder={COPY.placeholder} button={COPY.analyse} pressAt={P.click} busy={ramp(frame, P.click + 4, P.click + 14)} glow={ramp(frame, P.typeFrom, P.typeFrom + 20)} />
              </div>
            </At>
          )}
          {frame >= P.cursorFrom && <Cursor frame={frame} x={cur.x} y={cur.y} clicks={[P.click]} opacity={ramp(frame, P.cursorFrom, P.cursorFrom + 8)} />}
        </Camera>
      </Stage>
    </AbsoluteFill>
  )
}

function Line({ frame, at, text, color, italic }) {
  const words = text.split(' ')
  return (
    <div style={{ fontFamily: FONT.head, fontSize: 104, fontWeight: 600, lineHeight: 1.08, color, fontStyle: italic ? 'italic' : 'normal', letterSpacing: '-0.02em', textShadow: '0 10px 40px rgba(0,0,0,0.85)' }}>
      {words.map((w, i) => {
        const e = enter(frame, at + i * 5, 26)
        return (
          <span key={i} style={{ display: 'inline-block', margin: '0 0.18em', opacity: Math.min(1, e), transform: `translateY(${(1 - e) * 50}px)`, filter: `blur(${(1 - Math.min(1, e)) * 8}px)` }}>
            {w}
          </span>
        )
      })}
    </div>
  )
}

function Window({ w, style }) {
  return (
    <div
      style={{
        width: 440,
        borderRadius: 16,
        background: 'rgba(40, 36, 31, 0.92)',
        border: '1px solid rgba(255,255,255,0.08)',
        boxShadow: '0 24px 60px rgba(0,0,0,0.55)',
        overflow: 'hidden',
        fontFamily: FONT.ui,
        ...style,
      }}
    >
      <div style={{ height: 40, display: 'flex', alignItems: 'center', gap: 8, padding: '0 14px', background: 'rgba(255,255,255,0.04)', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        {['#7a6f5f', '#7a6f5f', '#7a6f5f'].map((c, i) => <span key={i} style={{ width: 11, height: 11, borderRadius: '50%', background: c }} />)}
        <span style={{ marginLeft: 10, fontSize: 17, color: C.dim, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{w.title}</span>
      </div>
      <div style={{ padding: '18px 20px 22px', fontSize: 21, color: C.faint, lineHeight: 1.5, fontFamily: `${FONT.ui}, ${FONT.arabic}` }}>
        {w.body}
        <div style={{ marginTop: 12, height: 9, width: '80%', borderRadius: 5, background: 'rgba(255,255,255,0.06)' }} />
        <div style={{ marginTop: 9, height: 9, width: '55%', borderRadius: 5, background: 'rgba(255,255,255,0.06)' }} />
      </div>
    </div>
  )
}
