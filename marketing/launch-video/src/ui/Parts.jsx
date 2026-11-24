import { C, FONT } from '../config'
import { press } from '../motion'

/** Frosted card, the app's glass surface. */
export function Glass({ children, style, glow }) {
  return (
    <div
      style={{
        background: C.surface,
        border: `1.5px solid ${C.border}`,
        borderRadius: 22,
        boxShadow: `0 30px 80px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.05)${glow ? `, 0 0 46px ${glow}` : ''}`,
        backdropFilter: 'blur(18px)',
        color: C.text,
        fontFamily: FONT.ui,
        ...style,
      }}
    >
      {children}
    </div>
  )
}

/** The mouse pointer, drawn as a vector so a zoom never blurs it. */
export function Cursor({ x, y, frame, clicks = [], opacity = 1 }) {
  const s = clicks.reduce((acc, c) => acc * press(frame, c), 1) ** 2
  const ring = clicks.map((c) => frame - c).find((d) => d >= 0 && d < 22)
  return (
    <div style={{ position: 'absolute', left: 960 + x, top: 540 + y, opacity, zIndex: 50 }}>
      {ring != null && (
        <div
          style={{
            position: 'absolute',
            left: -26 - ring,
            top: -26 - ring,
            width: 52 + ring * 2,
            height: 52 + ring * 2,
            borderRadius: '50%',
            border: `2px solid ${C.goldHi}`,
            opacity: 1 - ring / 22,
          }}
        />
      )}
      <svg width="38" height="46" viewBox="0 0 38 46" style={{ transform: `scale(${s})`, transformOrigin: '4px 4px', filter: 'drop-shadow(0 6px 10px rgba(0,0,0,0.5))' }}>
        <path d="M4 3 L4 36 L13 28 L19 42 L25 39.5 L19 26 L31 26 Z" fill="#fff" stroke="#111" strokeWidth="2.2" strokeLinejoin="round" />
      </svg>
    </div>
  )
}

/** On/off switch; `on` is 0..1 so it can be animated. */
export function Toggle({ on, scale = 1 }) {
  return (
    <div
      style={{
        width: 64 * scale,
        height: 36 * scale,
        borderRadius: 999,
        background: `color-mix(in srgb, ${C.gold} ${on * 100}%, #3a342c)`,
        position: 'relative',
        boxShadow: on > 0.5 ? `0 0 ${24 * on}px ${C.goldHi}aa, 0 0 ${60 * on}px ${C.gold}66` : 'none',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: 4 * scale,
          left: (4 + on * 28) * scale,
          width: 28 * scale,
          height: 28 * scale,
          borderRadius: '50%',
          background: '#fff8e8',
          boxShadow: '0 2px 6px rgba(0,0,0,0.4)',
        }}
      />
    </div>
  )
}

/** Small capitals label, the app's eyebrow. */
export function Eyebrow({ children, color = C.goldHi, style }) {
  return (
    <div style={{ fontFamily: FONT.label, fontSize: 20, letterSpacing: '0.18em', textTransform: 'uppercase', color, ...style }}>
      {children}
    </div>
  )
}

/** A check in a gold ring. */
export function Check({ size = 26, color = C.gold, p = 1 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 26 26">
      <circle cx="13" cy="13" r="12" fill={color} opacity={0.18 + 0.82 * p} />
      <path d="M7.5 13.5 L11.5 17.5 L19 9.5" fill="none" stroke="#1b1916" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="20" strokeDashoffset={20 * (1 - p)} />
    </svg>
  )
}
