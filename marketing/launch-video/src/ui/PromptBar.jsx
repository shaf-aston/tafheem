import { C, FONT } from '../config'
import { press } from '../motion'

// Tafheem's input bar: Arabic types in from the right, the gold button on the right.
export function PromptBar({ frame, text, placeholder, button, pressAt, busy = 0, width = 1000, rtl = true, glow = 0 }) {
  const p = pressAt != null ? press(frame, pressAt) : 1
  const sweep = ((frame * 1.6) % 140) - 20
  return (
    <div
      style={{
        width,
        height: 116,
        borderRadius: 30,
        background: 'rgba(30, 27, 23, 0.88)',
        border: `1.5px solid ${glow ? C.goldHi : 'rgba(236,202,119,0.28)'}`,
        boxShadow: `0 40px 90px rgba(0,0,0,0.5), 0 0 ${50 * glow}px ${C.gold}55, inset 0 1px 0 rgba(255,255,255,0.06)`,
        display: 'flex',
        alignItems: 'center',
        padding: '0 14px 0 34px',
        gap: 18,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {busy > 0 && (
        <div style={{ position: 'absolute', inset: 0, opacity: busy, background: `linear-gradient(100deg, transparent ${sweep}%, ${C.gold}22 ${sweep + 10}%, transparent ${sweep + 20}%)` }} />
      )}
      <div
        style={{
          flex: 1,
          direction: rtl ? 'rtl' : 'ltr',
          fontFamily: rtl ? FONT.arabic : FONT.ui,
          fontSize: rtl ? 38 : 38,
          color: text ? C.text : C.faint,
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          lineHeight: 1.6,
        }}
      >
        {text || <span style={{ fontFamily: FONT.ui, fontSize: 32 }}>{placeholder}</span>}
        {text && Math.floor(frame / 16) % 2 === 0 && !busy && (
          <span style={{ display: 'inline-block', width: 3, height: 46, background: C.goldHi, verticalAlign: '-10px', margin: '0 4px' }} />
        )}
      </div>
      <div
        style={{
          height: 86,
          padding: '0 34px',
          borderRadius: 22,
          background: `linear-gradient(180deg, ${C.goldHi}, ${C.gold})`,
          color: C.bg,
          fontFamily: FONT.ui,
          fontWeight: 650,
          fontSize: 30,
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          transform: `scale(${p})`,
          boxShadow: `0 8px 24px ${C.gold}55`,
        }}
      >
        {button}
        <svg width="26" height="26" viewBox="0 0 24 24"><path d="M5 12h13M13 6l6 6-6 6" fill="none" stroke={C.bg} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" /></svg>
      </div>
    </div>
  )
}
