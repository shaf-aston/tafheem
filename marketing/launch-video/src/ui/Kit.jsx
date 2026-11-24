import { AbsoluteFill, Img, staticFile } from 'remotion'
import { C, FONT } from '../config'
import { press } from '../motion'

/** The reference's backdrop: deep brown with slow ember glows and one black pocket. */
export function WarmBg({ frame, seed = 0, light = 1 }) {
  const t = frame / 60 + seed * 3.1
  const g1 = [28 + Math.sin(t * 0.5) * 8, 22 + Math.cos(t * 0.4) * 6]
  const g2 = [74 + Math.cos(t * 0.35) * 8, 70 + Math.sin(t * 0.45) * 8]
  const pk = [52 + Math.sin(t * 0.3 + 1) * 10, 48 + Math.cos(t * 0.38) * 8]
  return (
    <AbsoluteFill
      style={{
        background: [
          `radial-gradient(ellipse 34% 38% at ${pk[0]}% ${pk[1]}%, rgba(4,2,1,${0.72 * light}), transparent 72%)`,
          `radial-gradient(ellipse 55% 60% at ${g1[0]}% ${g1[1]}%, ${C.emberHi}, transparent 70%)`,
          `radial-gradient(ellipse 60% 55% at ${g2[0]}% ${g2[1]}%, rgba(92,34,9,0.95), transparent 72%)`,
          `radial-gradient(ellipse 40% 60% at 0% 60%, rgba(0,0,0,0.75), transparent 70%)`,
          C.base,
        ].join(','),
      }}
    />
  )
}

/** The glass orb, Tafheem's voice: saffron, peach and lavender turning inside a sphere. */
export function Orb({ size = 160, frame, blur = 0, glow = 1 }) {
  const rot = frame * 2.2
  return (
    <div style={{ width: size, height: size, position: 'relative', filter: blur ? `blur(${blur}px)` : undefined }}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          borderRadius: '50%',
          background: `conic-gradient(from ${rot}deg at ${50 + Math.sin(frame / 40) * 12}% ${50 + Math.cos(frame / 47) * 12}%, ${C.peach}, ${C.lavender}, #fbe9d7, ${C.saffron}, #6d74d4, ${C.peach})`,
          filter: `blur(${size * 0.1}px)`,
          transform: 'scale(0.94)',
          boxShadow: `0 0 ${size * 0.45 * glow}px rgba(246,196,140,${0.32 * glow})`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          borderRadius: '50%',
          background: `radial-gradient(circle at 50% 50%, rgba(255,240,228,0.05), rgba(255,240,228,0) 62%, rgba(255,255,255,0.22) 71%), radial-gradient(circle at ${36 + Math.sin(frame / 30) * 6}% ${30 + Math.cos(frame / 34) * 5}%, rgba(255,255,255,0.75), rgba(255,255,255,0) 38%), radial-gradient(circle at 70% 78%, rgba(20,8,30,0.45), transparent 55%)`,
          boxShadow: 'inset 0 0 0 1.5px rgba(255,255,255,0.35), inset -10px -14px 30px rgba(0,0,0,0.25)',
        }}
      />
    </div>
  )
}

/** The chat bubble the assistant speaks in: brown glass with a bright hairline. */
export function GlassBubble({ children, style }) {
  return (
    <div
      style={{
        background: 'linear-gradient(135deg, rgba(150,85,55,0.42), rgba(70,36,20,0.42))',
        border: `2px solid ${C.glassLine}`,
        borderRadius: 12,
        color: C.text,
        fontFamily: FONT.ui,
        boxShadow: '0 20px 60px rgba(0,0,0,0.35)',
        ...style,
      }}
    >
      {children}
    </div>
  )
}

/** The user's bubble: flat and light. */
export function LightBubble({ children, style }) {
  return (
    <div style={{ background: C.cream, borderRadius: 12, color: '#4a4440', fontFamily: FONT.ui, boxShadow: '0 20px 60px rgba(0,0,0,0.35)', ...style }}>
      {children}
    </div>
  )
}

/** The loading spinner: 8 ticks, one bright, turning. */
export function Spinner({ frame, size = 26, color = '#fff' }) {
  const lead = Math.floor(frame / 5) % 8
  return (
    <svg width={size} height={size} viewBox="-12 -12 24 24">
      {Array.from({ length: 8 }, (_, i) => {
        const a = (i / 8) * Math.PI * 2
        const age = (lead - i + 8) % 8
        return (
          <line
            key={i}
            x1={Math.cos(a) * 5}
            y1={Math.sin(a) * 5}
            x2={Math.cos(a) * 10}
            y2={Math.sin(a) * 10}
            stroke={color}
            strokeWidth="2.4"
            strokeLinecap="round"
            opacity={1 - age * 0.11}
          />
        )
      })}
    </svg>
  )
}

/** Status pill with spinner: grey glass on dark shots, white on busy ones. */
export function Pill({ frame, text, light = false, scale = 1 }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 18 * scale,
        padding: `${20 * scale}px ${44 * scale}px`,
        borderRadius: 16 * scale,
        background: light ? '#fff' : 'rgba(150,140,136,0.82)',
        color: light ? '#4a4440' : '#fff',
        fontFamily: FONT.ui,
        fontSize: 32 * scale,
        letterSpacing: -0.6,
        boxShadow: '0 20px 60px rgba(0,0,0,0.35)',
        whiteSpace: 'nowrap',
      }}
    >
      <Spinner frame={frame} size={28 * scale} color={light ? '#8a817c' : '#fff'} />
      {text}
    </div>
  )
}

/** On/off switch; `on` runs 0..1 so the knob can slide. */
export function Toggle({ on, scale = 1 }) {
  const w = 64 * scale
  const h = 36 * scale
  const k = h - 8 * scale
  return (
    <div
      style={{
        width: w,
        height: h,
        borderRadius: 999,
        background: `color-mix(in srgb, ${C.saffron} ${on * 100}%, rgba(255,255,255,0.16))`,
        position: 'relative',
        flex: 'none',
        boxShadow: on > 0.5 ? `0 0 ${18 * scale}px rgba(244,145,59,0.45)` : 'none',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: 4 * scale,
          left: 4 * scale + on * (w - k - 8 * scale),
          width: k,
          height: k,
          borderRadius: '50%',
          background: '#fff',
          boxShadow: '0 2px 6px rgba(0,0,0,0.35)',
        }}
      />
    </div>
  )
}

/** The pointer, as a vector so zooms never blur it; `hand` swaps in the grab hand. */
export function Cursor({ x, y, frame, clicks = [], hand = false, size = 1 }) {
  const s = clicks.reduce((acc, c) => acc * press(frame, c), 1) ** 3 * size
  return (
    <div style={{ position: 'absolute', left: 960 + x, top: 540 + y, zIndex: 50, transform: `scale(${s})`, transformOrigin: '0 0' }}>
      {hand ? (
        <svg width="56" height="58" viewBox="0 0 56 58" style={{ transform: 'translate(-22px,-14px)', filter: 'drop-shadow(0 6px 10px rgba(0,0,0,0.5))' }}>
          <path
            d="M14 26 V12 a4 4 0 0 1 8 0 V24 V8 a4 4 0 0 1 8 0 V24 V10 a4 4 0 0 1 8 0 V26 V16 a4 4 0 0 1 8 0 V36 c0 10 -7 18 -17 18 h-4 c-7 0 -11 -4 -15 -10 l-7 -11 a4 4 0 0 1 6 -5 z"
            fill="#fff"
            stroke="#111"
            strokeWidth="2.6"
            strokeLinejoin="round"
          />
          <path d="M22 26 V36 M30 25 V36 M38 26 V36" stroke="#111" strokeWidth="2.2" strokeLinecap="round" />
        </svg>
      ) : (
        <svg width="38" height="46" viewBox="0 0 38 46" style={{ transform: 'translate(-4px,-3px)', filter: 'drop-shadow(0 6px 10px rgba(0,0,0,0.5))' }}>
          <path d="M4 3 L4 36 L13 28 L19 42 L25 39.5 L19 26 L31 26 Z" fill="#fff" stroke="#111" strokeWidth="2.2" strokeLinejoin="round" />
        </svg>
      )}
    </div>
  )
}

/** The round letter badge on every tool card (saffron-peach disc, dark glyph). */
export function Badge({ glyph, size = 56 }) {
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        background: `radial-gradient(circle at 35% 30%, #ffd9a8, ${C.peach} 60%, #e9a865)`,
        display: 'grid',
        placeItems: 'center',
        color: '#2a1408',
        fontFamily: FONT.arabic,
        fontWeight: 700,
        fontSize: size * 0.56,
        lineHeight: 1,
        paddingBottom: size * 0.08,
        boxSizing: 'border-box',
        flex: 'none',
      }}
    >
      {glyph}
    </div>
  )
}

/** One tool card, laid out like the reference's agent cards. */
export function ToolCard({ card, on = 1, w = 440, k = 1 }) {
  const u = (n) => n * k
  return (
    <div
      style={{
        width: u(w),
        padding: `${u(28)}px ${u(28)}px ${u(22)}px`,
        boxSizing: 'border-box',
        borderRadius: u(18),
        background: 'linear-gradient(160deg, rgba(34,22,16,0.92), rgba(14,9,7,0.92))',
        border: `1px solid ${C.line}`,
        boxShadow: '0 30px 80px rgba(0,0,0,0.45)',
        color: C.text,
        fontFamily: FONT.ui,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Badge glyph={card.glyph} size={u(56)} />
        <div style={{ display: 'flex', alignItems: 'center', gap: u(14) }}>
          <span style={{ fontSize: u(12), letterSpacing: 0.6, color: C.dim }}>OFFLINE</span>
          <Toggle on={on} scale={k} />
        </div>
      </div>
      <div style={{ marginTop: u(34), fontSize: u(12.5), letterSpacing: 0.8, color: C.dim }}>{card.eyebrow}</div>
      <div style={{ marginTop: u(8), fontSize: u(34), letterSpacing: -0.8, fontWeight: 500 }}>{card.title}</div>
      <div style={{ marginTop: u(6), fontSize: u(19), color: '#c9c0e8' }}>{card.sub}</div>
      <div style={{ marginTop: u(22), borderTop: `1px solid ${C.line}`, paddingTop: u(14), display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span
          style={{
            background: C.peach,
            color: '#2a1408',
            borderRadius: 999,
            padding: `${u(3)}px ${u(10)}px`,
            fontSize: u(15),
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: u(6),
          }}
        >
          <span style={{ fontSize: u(11) }}>▲</span> Ready
        </span>
        <span style={{ fontSize: u(14), color: C.dim }}>{card.note}</span>
      </div>
    </div>
  )
}

/** A square app tile with a glyph, as in the icon row and the page footer. */
export function Tile({ glyph, tone, size = 72, label, labelColor = C.dim }) {
  const bg = { saffron: C.saffron, cream: C.cream, peach: C.peach, lavender: C.lavender, navy: C.navy, ink: '#2b2725' }[tone]
  const fg = ['cream', 'peach'].includes(tone) ? '#5a2c10' : '#fff'
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: size * 0.16 }}>
      <div
        style={{
          width: size,
          height: size,
          borderRadius: size * 0.22,
          background: bg,
          color: fg,
          display: 'grid',
          placeItems: 'center',
          fontFamily: FONT.arabic,
          fontWeight: 700,
          fontSize: size * (glyph.length > 4 ? 0.24 : 0.3),
          lineHeight: 1,
          boxShadow: '0 10px 24px rgba(0,0,0,0.3)',
        }}
      >
        {glyph}
      </div>
      {label && <div style={{ fontFamily: FONT.ui, fontSize: size * 0.17, color: labelColor }}>{label}</div>}
    </div>
  )
}

/**
 * A crop of one of the app's real images (public/img). zoom > 1 enlarges it inside
 * the frame; ox/oy (0-100) pick which part shows, like background-position.
 */
export function Pic({ src, w, h, zoom = 1, ox = 50, oy = 50, style }) {
  const iw = w * zoom
  const ih = h * zoom
  return (
    <div style={{ width: w, height: h, overflow: 'hidden', position: 'relative', flex: 'none', ...style }}>
      <Img
        src={staticFile(`img/${src}`)}
        style={{ position: 'absolute', width: iw, height: ih, left: -(iw - w) * (ox / 100), top: -(ih - h) * (oy / 100), objectFit: 'cover' }}
      />
    </div>
  )
}
