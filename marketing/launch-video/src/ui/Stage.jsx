import { AbsoluteFill, useVideoConfig } from 'remotion'

// The design canvas is 1920 × 1080 with every key element inside the centre
// SAFE × 1080. Stage scales that canvas by the short side and centres it, so the
// same shots render as 16:9, 9:16 and 1:1 without a second layout.
export const SAFE = 1440

// Portrait frames show a narrower 1180 px slice so the content fills more of the phone screen;
// wide rows shrink back to fit through useFit.
function stageScale(width, height) {
  return Math.min(width / (height > width * 1.2 ? 1180 : SAFE), height / 1080)
}

export function Stage({ children, style }) {
  const { width, height } = useVideoConfig()
  const s = stageScale(width, height)
  return (
    <AbsoluteFill style={{ overflow: 'hidden', ...style }}>
      <div
        style={{
          position: 'absolute',
          left: width / 2,
          top: height / 2,
          width: 1920,
          height: 1080,
          marginLeft: -960,
          marginTop: -540,
          transform: `scale(${s})`,
        }}
      >
        {children}
      </div>
    </AbsoluteFill>
  )
}

/** Full-frame layer in real output pixels, for backgrounds and patterns that must reach every edge. */
export function Bleed({ children, style }) {
  return <AbsoluteFill style={{ overflow: 'hidden', ...style }}>{children}</AbsoluteFill>
}

/** Places a child by its centre, measured from the canvas centre. */
export function At({ x = 0, y = 0, children, style }) {
  return (
    <div style={{ position: 'absolute', left: 960 + x, top: 540 + y, transform: 'translate(-50%, -50%)', ...style }}>
      {children}
    </div>
  )
}

/** One camera per shot: scale and pan around the canvas centre. */
export function Camera({ scale = 1, x = 0, y = 0, children, style }) {
  return (
    <AbsoluteFill style={{ transform: `scale(${scale}) translate(${-x}px, ${-y}px)`, transformOrigin: '960px 540px', ...style }}>
      {children}
    </AbsoluteFill>
  )
}

/** Scale that keeps a row `w` design-px wide inside the frame on narrow (9:16, 1:1) outputs; 1 on 16:9. */
export function useFit(w, margin = 60) {
  const { width, height } = useVideoConfig()
  const s = stageScale(width, height)
  return Math.min(1, (width / s - 2 * margin) / w)
}
