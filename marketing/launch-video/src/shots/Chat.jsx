// Shots 4-5: the first exchange, then the prompt with the ayah pictures dragged in.
import { C, COPY, FONT, STREAM } from '../config'
import T from '../timeline.json'
import { Stage, Bleed, At, Camera } from '../ui/Stage'
import { WarmBg, Orb, GlassBubble, LightBubble, Cursor, Pic } from '../ui/Kit'
import { enter, mix, ramp, typed, cursorAt, easeOut, easeInOut } from '../motion'

const caret = (frame, end) => (frame < end + 24 && Math.floor(frame / 14) % 2 === 0 ? '|' : '')

// Shot 4. Tafheem says salaam; the student asks.
export function Chat({ frame }) {
  const f = frame - 245
  const [ba, bb] = T.cue.botType
  const [ua, ub] = T.cue.userType
  const bot = enter(frame, 247, 26)
  const user = enter(frame, T.cue.userIn, 26)
  const text = { fontSize: 40, lineHeight: 1.12, letterSpacing: -1 }
  return (
    <>
      <Bleed>
        <WarmBg frame={frame} seed={2} />
      </Bleed>
      <Stage>
        <Camera scale={1.02 + f * 0.0006} x={-40 - f * 0.25} y={-70 + f * 0.15}>
          <At x={-590} y={-196}>
            <Orb frame={frame} size={70} />
          </At>
          <div style={{ position: 'absolute', left: 960 - 530, top: 540 - 250, transformOrigin: '0 50%', transform: `scale(${0.6 + 0.4 * bot})`, opacity: Math.min(1, bot * 2) }}>
            <GlassBubble style={{ width: 640, minHeight: 126, padding: '20px 30px', boxSizing: 'border-box', ...text }}>
              {typed(COPY.bot, frame, ba, bb)}
              {caret(frame, bb)}
            </GlassBubble>
          </div>
          <div
            style={{
              position: 'absolute',
              left: 960 - 40,
              top: 540 - 60 + (1 - user) * 60,
              opacity: Math.min(1, user * 2),
              transform: `scale(${0.9 + 0.1 * user})`,
              transformOrigin: '100% 50%',
            }}
          >
            <LightBubble style={{ width: 580, minHeight: 126, padding: '20px 34px', boxSizing: 'border-box', ...text }}>
              {typed(COPY.user, frame, ua, ub)}
              {frame >= ua && caret(frame, ub)}
            </LightBubble>
          </div>
        </Camera>
      </Stage>
    </>
  )
}

const Arrow = () => (
  <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 19V5M5 12l7-7 7 7" />
  </svg>
)

// The three pictures dragged in: the Met folio and two of the app's own screens.
const PICS = [
  { src: 'folio.jpg', zoom: 1.5, ox: 50, oy: 30 },
  { src: 'quran.jpg', zoom: 2.6, ox: 66, oy: 92 },
  { src: 'nahw.jpg', zoom: 2.4, ox: 100, oy: 23 },
]

// Shot 5. Type the ask, drag the ayah in, send.
export function Prompt({ frame }) {
  const f = frame - 360
  const [pa, pb] = T.cue.promptType
  const [da, db] = T.cue.drag
  const drop = T.cue.drop
  const send = T.cue.sendClick
  const barIn = enter(frame, 360, 24)
  const tray = ramp(frame, db - 18, drop + 4, easeOut)
  const lift = mix(frame, [send + 4, 510], [0, -200], easeInOut)
  const BAR_Y = 150
  const W = 1160
  // Held stack: rides with the hand from off-frame left to above the tray.
  const carry = ramp(frame, da, db, easeInOut)
  const hx = mix(carry, [0, 1], [-1150, -420], (t) => t)
  const hy = mix(carry, [0, 1], [-330, -40], (t) => t) + Math.sin(carry * Math.PI) * -60
  const settle = ramp(frame, drop, drop + 14, easeOut)
  const hand = frame < drop + 6
  const cur = hand
    ? { x: hx + 120, y: hy + 80 }
    : cursorAt(frame, [
        { f: drop + 6, x: hx + 120, y: hy + 80 },
        { f: send - 2, x: W / 2 - 60, y: BAR_Y + 4, h: 18 },
      ])
  return (
    <>
      <Bleed>
        <WarmBg frame={frame} seed={2.6} />
      </Bleed>
      <Stage>
        <Camera scale={1.02 + f * 0.0004} y={-lift * 0.15}>
          <div style={{ position: 'absolute', inset: 0, transform: `translateY(${lift}px)` }}>
            {/* attachment tray */}
            <div
              style={{
                position: 'absolute',
                left: 960 - W / 2,
                top: 540 + BAR_Y - 75 - 170 * tray,
                width: W,
                height: 190 * tray + 20,
                borderRadius: 18,
                background: 'linear-gradient(90deg, rgba(60,38,28,0.75), rgba(30,22,20,0.7), rgba(70,44,30,0.7))',
                opacity: tray,
              }}
            />
            {/* the bar */}
            <At y={BAR_Y}>
              <GlassBubble
                style={{
                  width: W,
                  height: 150,
                  borderRadius: 18,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0 34px 0 44px',
                  boxSizing: 'border-box',
                  background: 'linear-gradient(90deg, rgba(110,60,40,0.55), rgba(40,26,22,0.65) 60%, rgba(90,50,32,0.55))',
                  transform: `scale(${0.94 + 0.06 * barIn})`,
                  opacity: barIn,
                }}
              >
                <span style={{ fontSize: 42, letterSpacing: -1 }}>
                  {typed(COPY.prompt, frame, pa, pb)}
                  {caret(frame, pb)}
                </span>
                <div
                  style={{
                    width: 82,
                    height: 82,
                    borderRadius: 12,
                    background: frame >= send && frame < send + 10 ? C.saffron : 'rgba(30,24,22,0.85)',
                    display: 'grid',
                    placeItems: 'center',
                  }}
                >
                  <Arrow />
                </div>
              </GlassBubble>
            </At>
            {/* the pictures: a stack in the hand, then three thumbnails in the tray */}
            {PICS.map((p, i) => {
              const sx = hx - 130 + i * 52
              const sy = hy - 110 + i * 40
              const tx = -W / 2 + 30 + i * 196
              const ty = BAR_Y - 75 - 160
              const x = sx + (tx - sx) * settle
              const y = sy + (ty - sy) * settle
              const w = 270 + (172 - 270) * settle
              const h = 200 + (130 - 200) * settle
              return (
                <div
                  key={p.src}
                  style={{
                    position: 'absolute',
                    left: 960 + x,
                    top: 540 + y,
                    opacity: frame < da ? 0 : 1,
                    borderRadius: 8 * settle + 2,
                    overflow: 'hidden',
                    boxShadow: '0 16px 40px rgba(0,0,0,0.45)',
                    zIndex: 10 - i,
                  }}
                >
                  <Pic src={p.src} w={w} h={h} zoom={p.zoom} ox={p.ox} oy={p.oy} />
                </div>
              )
            })}
            {/* first lines of the analysis start under the bar once it is sent */}
            <div
              style={{
                position: 'absolute',
                left: 960 - W / 2 + 10,
                top: 540 + BAR_Y + 110,
                opacity: ramp(frame, send + 4, 510),
                fontFamily: FONT.mono,
                fontSize: 26,
                lineHeight: 1.5,
                color: C.dim,
                whiteSpace: 'pre',
              }}
            >
              {STREAM.slice(0, 5).map((l) => l.join('')).join('\n')}
            </div>
          </div>
          <Cursor x={cur.x} y={cur.y + (hand ? 0 : 0)} frame={frame} clicks={[send]} hand={hand} />
        </Camera>
      </Stage>
    </>
  )
}
