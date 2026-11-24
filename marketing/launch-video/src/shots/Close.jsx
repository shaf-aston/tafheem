// Shots 15-16: the answer to the opening question, then the logo.
import { AbsoluteFill } from 'remotion'
import { C, COPY, FONT } from '../config'
import T from '../timeline.json'
import { Stage, Bleed, At, Camera, useFit } from '../ui/Stage'
import { WarmBg } from '../ui/Kit'
import { starPath } from './Open'
import { enter, mix, ramp, typed, press, easeOut, easeIn, easeInOut } from '../motion'

const Mic = () => (
  <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#9a938f" strokeWidth="1.8" strokeLinecap="round">
    <rect x="9" y="3" width="6" height="11" rx="3" />
    <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
  </svg>
)

// Shot 15. The student answers the question the video opened with; the camera
// leans in on the send button, as the reference does.
export function Final({ frame }) {
  const f = frame - 1230
  const [a, b] = T.cue.finalType
  const click = T.cue.finalClick
  const lean = ramp(frame, 1286, 1302, easeOut)
  const scale = 1 + f * 0.0006 + lean * 1.05
  const x = lean * 420
  const W = 1180
  const fit = useFit(1240)
  const btn = press(frame, click) ** 3
  return (
    <>
      <Bleed>
        <WarmBg frame={frame} seed={8} />
      </Bleed>
      <Stage>
        <Camera scale={scale * fit} x={x} y={lean * 10}>
          <At>
            <div
              style={{
                width: W,
                padding: 10,
                borderRadius: 26,
                background: 'rgba(255,255,255,0.55)',
                boxShadow: '0 40px 120px rgba(0,0,0,0.5)',
                opacity: enter(frame, 1230, 20),
              }}
            >
              <div style={{ background: '#fff', borderRadius: 18, fontFamily: FONT.ui, color: '#2f2b29', overflow: 'hidden' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 26, height: 116, padding: '0 22px 0 30px' }}>
                  <span style={{ fontSize: 40, color: '#9a938f', fontWeight: 300 }}>+</span>
                  <span style={{ flex: 1, fontSize: 37, letterSpacing: -1, whiteSpace: 'nowrap' }}>
                    {typed(COPY.final, frame, a, b)}
                    <span style={{ opacity: Math.floor(frame / 14) % 2 === 0 ? 1 : 0 }}>|</span>
                  </span>
                  <Mic />
                  <div
                    style={{
                      width: 76,
                      height: 76,
                      borderRadius: 14,
                      background: frame >= click && frame < click + 10 ? C.saffron : '#2f2b29',
                      display: 'grid',
                      placeItems: 'center',
                      transform: `scale(${btn})`,
                    }}
                  >
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 19V5M5 12l7-7 7 7" />
                    </svg>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 0, borderTop: '1px solid #ece8e6', fontSize: 22, color: '#9a938f', padding: '12px 30px 14px' }}>
                  {COPY.finalHint.map((h, i) => (
                    <span key={h} style={{ paddingRight: 22, marginRight: 22, borderRight: i < COPY.finalHint.length - 1 ? '1px solid #e2ddda' : 'none' }}>
                      {h}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </At>
        </Camera>
      </Stage>
    </>
  )
}

// Shot 16. The reference's ✕ turns into a +; ours turns on into the 8-point star.
export function Logo({ frame }) {
  const m = T.cue.logoMorph
  const turn = enter(frame, m, 26)
  const draw = ramp(frame, m + 10, m + 34, easeOut)
  const name = typed(COPY.name, frame, 1352, 1374)
  const url = ramp(frame, 1396, 1414, easeOut)
  const zoom = mix(frame, [1350, 1440], [1.04, 1], easeOut)
  const dots = [0, 1, 2, 3]
  const S = 46
  return (
    <>
      <Bleed>
        <AbsoluteFill style={{ background: C.paper }} />
      </Bleed>
      <Stage>
        <Camera scale={zoom}>
          {dots.map((i) => {
            const ang = (i * Math.PI) / 2 + (frame - 1350) * 0.006
            return (
              <At key={i} x={-10 + Math.cos(ang) * 330} y={-20 + Math.sin(ang) * 112}>
                <div style={{ width: 18, height: 18, borderRadius: '50%', background: '#fffaf3', boxShadow: '2px 4px 8px rgba(190,120,40,0.45)' }} />
              </At>
            )
          })}
          <At y={-20}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 30 }}>
              <svg width={S * 2.4} height={S * 2.4} viewBox={`${-S * 1.2} ${-S * 1.2} ${S * 2.4} ${S * 2.4}`} style={{ overflow: 'visible' }}>
                <g transform={`rotate(${45 * (1 - turn)})`} stroke={C.saffron} strokeWidth="7" strokeLinecap="round" fill="none">
                  <path d={`M0 ${-S * 0.72}V${S * 0.72}M${-S * 0.72} 0H${S * 0.72}`} />
                </g>
                <path
                  d={starPath(0, 0, S, 0, 1)}
                  stroke={C.saffron}
                  strokeWidth="6"
                  strokeLinejoin="round"
                  fill="none"
                  pathLength="1"
                  strokeDasharray="1"
                  strokeDashoffset={1 - draw}
                />
              </svg>
              <span style={{ fontFamily: FONT.ui, fontSize: 92, fontWeight: 700, letterSpacing: -3, color: C.saffron, minWidth: 380 }}>{name}</span>
            </div>
          </At>
          <At y={160}>
            <div style={{ fontFamily: FONT.ui, fontSize: 30, color: '#8c8480', letterSpacing: 0.2, opacity: url, transform: `translateY(${(1 - url) * 14}px)` }}>
              {COPY.url}
            </div>
          </At>
        </Camera>
      </Stage>
    </>
  )
}
