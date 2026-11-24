import { AbsoluteFill } from 'remotion'
import T from '../timeline.json'
import { C, COPY, FONT } from '../config'
import { enter, exit, mix, ramp, typed, drift, easeOut, easeIn } from '../motion'
import { Stage, At, Camera } from '../ui/Stage'
import { Backdrop, Paper } from '../ui/Backdrop'
import { Star } from '../ui/Star'
import { Mark } from '../ui/Mark'

const H = T.hook

// Scene 1 · Hook. Paper and a turning star; the first word revealed, "Read.";
// then the question every reader of a translation knows. An iris of ink opens
// from the star's centre onto "Meet Tafheem".
export function Hook({ frame }) {
  const irisR = mix(frame, [H.iris, H.iris + 20], [0, 1300], easeIn)
  return (
    <AbsoluteFill>
      <Stage>
        <PaperSide frame={frame} />
        {frame >= H.iris && (
          <AbsoluteFill style={{ clipPath: `circle(${irisR}px at 960px 540px)` }}>
            <MeetSide frame={frame} />
          </AbsoluteFill>
        )}
      </Stage>
    </AbsoluteFill>
  )
}

function PaperSide({ frame }) {
  const inA = enter(frame, H.ayahIn, 40)
  const gloss = enter(frame, H.ayahIn + 26)
  const q = typed(COPY.hookQuestion, frame, H.typeFrom, H.typeTo)
  const caret = frame >= H.typeFrom - 10 && Math.floor(frame / 16) % 2 === 0
  const rise = mix(frame, [H.typeFrom - 14, H.typeFrom + 10], [0, -70], easeOut)
  const d = drift(frame, 1, 3)
  return (
    <Camera frame={frame} scale={mix(frame, [0, H.iris + 20], [1.0, 1.14], easeOut)} push={0}>
      <Paper frame={frame} />
      <At>
        <svg width="1500" height="1500" viewBox="-750 -750 1500 1500" style={{ transform: `rotate(${frame * 0.06}deg)` }}>
          {[620, 470, 330, 200].map((r, i) => {
            const p = ramp(frame, 4 + i * 6, 70 + i * 6, easeOut)
            return <Star key={r} r={r} stroke={C.paperGold} width={1.6} opacity={0.28 - i * 0.03} dash={4 * r} offset={4 * r * (1 - p)} inner={0.78} />
          })}
          {[...Array(8)].map((_, i) => {
            const a = (Math.PI / 4) * i
            return <circle key={i} cx={Math.cos(a) * 470} cy={Math.sin(a) * 470} r={5} fill={C.paperGold} opacity={0.35 * ramp(frame, 30 + i * 3, 50 + i * 3)} />
          })}
        </svg>
      </At>
      <At y={-40 + rise + d.y} x={d.x}>
        <div
          style={{
            fontFamily: FONT.mushaf,
            fontSize: 220,
            color: C.paperText,
            transform: `scale(${0.7 + 0.3 * inA})`,
            opacity: inA,
            filter: `blur(${(1 - inA) * 14}px)`,
            lineHeight: 1.2,
            direction: 'rtl',
          }}
        >
          {COPY.hookWord}
        </div>
      </At>
      <At y={110 + rise}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 22, opacity: gloss, transform: `translateY(${(1 - gloss) * 20}px)` }}>
          <span style={{ fontFamily: FONT.head, fontSize: 64, fontStyle: 'italic', color: C.paperText }}>{COPY.hookGloss}</span>
          <span style={{ fontFamily: FONT.label, fontSize: 18, letterSpacing: '0.2em', color: C.paperGold, textTransform: 'uppercase' }}>{COPY.hookRef}</span>
        </div>
      </At>
      <At y={220}>
        <div style={{ fontFamily: FONT.head, fontSize: 60, fontWeight: 500, color: C.paperText, whiteSpace: 'pre', letterSpacing: '-0.01em' }}>
          {q}
          <span style={{ display: 'inline-block', width: 4, height: 58, marginLeft: 6, background: C.paperGold, verticalAlign: '-8px', opacity: caret ? 1 : 0 }} />
        </div>
      </At>
    </Camera>
  )
}

function MeetSide({ frame }) {
  const m = enter(frame, H.meet, 34)
  const words = enter(frame, H.meet + 14, 34)
  const ar = enter(frame, H.meet + 34)
  const out = exit(frame, T.scenes.hook[1] - 14, 14)
  const gap = 150 + 120 * words
  return (
    <AbsoluteFill style={{ opacity: out }}>
      <Backdrop />
      <Camera frame={frame - H.meet} scale={mix(frame, [H.meet, T.scenes.hook[1]], [1, 1.06])} push={0}>
        <At x={-gap - 130}>
          <div style={{ fontFamily: FONT.head, fontSize: 132, fontWeight: 400, color: C.text, opacity: words, filter: `blur(${(1 - words) * 10}px)` }}>{COPY.meet}</div>
        </At>
        <At x={-120}>
          <div style={{ transform: `scale(${m}) rotate(${(1 - m) * -40}deg)`, filter: `drop-shadow(0 0 ${40 * m}px ${C.gold}88)` }}>
            <Mark size={210} draw={ramp(frame, H.meet, H.meet + 30)} fill={ramp(frame, H.meet + 16, H.meet + 40)} plate={C.bg} />
          </div>
        </At>
        <At x={gap + 30}>
          <div style={{ fontFamily: FONT.head, fontSize: 132, fontWeight: 600, color: C.goldHi, opacity: words, filter: `blur(${(1 - words) * 10}px)` }}>{COPY.name}</div>
        </At>
        <At y={170}>
          <div style={{ fontFamily: FONT.arabic, fontSize: 54, color: C.dim, opacity: ar, letterSpacing: 0, transform: `translateY(${(1 - ar) * 16}px)` }}>
            {COPY.nameAr} <span style={{ fontFamily: FONT.ui, fontSize: 26, color: C.faint, marginLeft: 14 }}>making it understood</span>
          </div>
        </At>
      </Camera>
    </AbsoluteFill>
  )
}
