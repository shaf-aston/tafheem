// Shots 1-3: the question in the star tunnel, "Meet Tafheem", the first "Salaam".
import { AbsoluteFill, useVideoConfig } from 'remotion'
import { C, COPY, FONT } from '../config'
import T from '../timeline.json'
import { Stage, Bleed, At, Camera, useFit } from '../ui/Stage'
import { WarmBg, Orb, GlassBubble } from '../ui/Kit'
import { enter, mix, ramp, typed, easeIn, easeOut } from '../motion'
import { SAFE } from '../ui/Stage'

/** 8-point star (two squares) as an SVG path, squashed in y for the tilt. */
export function starPath(cx, cy, r, rot = 0, squash = 1) {
  const pts = []
  const ri = r * 0.7654
  for (let i = 0; i < 16; i++) {
    const a = rot + (i * Math.PI) / 8 - Math.PI / 2
    const rr = i % 2 === 0 ? r : ri
    pts.push(`${(cx + Math.cos(a) * rr).toFixed(1)},${(cy + Math.sin(a) * rr * squash).toFixed(1)}`)
  }
  return `M${pts.join('L')}Z`
}

// Shot 1. The reference opens in a cut-paper ring tunnel; ours is cut from
// 8-point stars, each step a little turned, with the question typed in the middle.
export function Tunnel({ frame }) {
  const { width: W, height: H } = useVideoConfig()
  const u = Math.min(W / SAFE, H / 1080)
  const f = frame
  const [a, b] = T.cue.tunnelType
  const zoom = mix(f, [0, 100, 120], [1, 1.22, 5.5], easeIn)
  const cx = W / 2
  const cy = H / 2
  const levels = [4300, 2500, 1480, 860, 470]
  return (
    <Bleed>
      <AbsoluteFill style={{ background: '#fbe6d8' }} />
      <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#d41f1a" />
            <stop offset="0.1" stopColor="#ec4f24" />
            <stop offset="0.3" stopColor="#f59468" />
            <stop offset="0.55" stopColor="#f9cdb5" />
            <stop offset="1" stopColor="#fbe6d8" />
          </linearGradient>
          <radialGradient id="face" cx="0.5" cy="0.42" r="0.6">
            <stop offset="0.55" stopColor="#fbe6d8" />
            <stop offset="1" stopColor="#f7cdb9" />
          </radialGradient>
          <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation={18 * u} />
          </filter>
        </defs>
        <g transform={`translate(${cx} ${cy}) scale(${zoom}) translate(${-cx} ${-cy})`}>
          {levels.map((r0, i) => {
            const r = r0 * u
            const rot = (i - 2) * 0.07 + f * 0.0011 * (i % 2 ? 1 : -1)
            const h = r * 0.15
            return (
              <g key={i}>
                <path d={starPath(cx, cy, r, rot, 0.58)} fill="url(#wall)" />
                <path d={starPath(cx, cy + h * 0.6, r * 0.985, rot, 0.58)} fill="#c9401c" opacity="0.35" filter="url(#soft)" />
                <path d={starPath(cx, cy + h, r * 0.97, rot, 0.58)} fill="url(#face)" />
              </g>
            )
          })}
        </g>
      </svg>
      <Stage>
        <Camera scale={zoom}>
          {[0, 1, 2, 3].map((i) => {
            const ang = (i * Math.PI) / 2 + f * 0.012
            return (
              <At key={i} x={Math.cos(ang) * 560} y={Math.sin(ang) * 210 + 30}>
                <div style={{ width: 22, height: 22, borderRadius: '50%', background: '#fff', boxShadow: '0 4px 10px rgba(180,60,20,0.35)' }} />
              </At>
            )
          })}
          <At y={30}>
            <div style={{ fontFamily: FONT.ui, fontSize: 58, letterSpacing: -1.4, fontWeight: 500, color: '#8a2d10', whiteSpace: 'nowrap' }}>
              {typed(COPY.question, f, a, b)}
              <span style={{ opacity: f < b + 20 && Math.floor(f / 15) % 2 === 0 ? 1 : 0 }}>|</span>
            </div>
          </At>
        </Camera>
      </Stage>
    </Bleed>
  )
}

// Shot 2. "Meet [orb] Tafheem", pulled into focus from a blur.
export function Meet({ frame }) {
  const f = frame - 120
  const focus = ramp(f, 0, 34, easeOut)
  const blur = (1 - focus) * 16
  const s = 1.08 - 0.08 * focus + f * 0.0004
  const fit = useFit(1520)
  const words = { fontFamily: FONT.ui, fontSize: 132, letterSpacing: -4, fontWeight: 500, color: C.text, filter: `blur(${blur}px)` }
  return (
    <>
      <Bleed>
        <WarmBg frame={frame} seed={1} />
      </Bleed>
      <Stage>
        <Camera scale={s * fit}>
          <At x={-420}>
            <div style={words}>{COPY.meet}</div>
          </At>
          <At x={0}>
            <Orb frame={frame} size={260} blur={blur * 0.7} />
          </At>
          <At x={470}>
            <div style={words}>{COPY.name}</div>
          </At>
        </Camera>
      </Stage>
    </>
  )
}

// Shot 3. The orb steps aside and its first word fills a big bubble.
export function Hello({ frame }) {
  const f = frame - 200
  const [a, b] = T.cue.helloType
  const t = enter(frame, 200, 26)
  const orbX = mix(f, [0, 16], [0, -470], easeOut)
  const orbS = mix(f, [0, 16], [260, 110], easeOut)
  return (
    <>
      <Bleed>
        <WarmBg frame={frame} seed={1.2} />
      </Bleed>
      <Stage>
        <Camera scale={1 + f * 0.001}>
          <At x={orbX}>
            <Orb frame={frame} size={orbS} />
          </At>
          <At x={60}>
            <GlassBubble
              style={{
                width: 760,
                height: 300,
                display: 'flex',
                alignItems: 'center',
                padding: '0 56px',
                boxSizing: 'border-box',
                transform: `scale(${0.3 + 0.7 * t})`,
                transformOrigin: '0% 50%',
                opacity: Math.min(1, t * 2),
              }}
            >
              <span style={{ fontSize: 170, letterSpacing: -6, fontWeight: 500, lineHeight: 1 }}>{typed(COPY.hello, frame, a, b)}</span>
            </GlassBubble>
          </At>
        </Camera>
      </Stage>
    </>
  )
}
