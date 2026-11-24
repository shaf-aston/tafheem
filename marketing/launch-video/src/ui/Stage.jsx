import { AbsoluteFill, useVideoConfig } from 'remotion'

// The design canvas is 1920 × 1080 with every key element inside the centre
// 1180 × 1080. Stage scales that canvas by the short side and centres it, so the
// same scenes render as 16:9, 9:16 and 1:1 without a second layout.
export function Stage({ children }) {
  const { width, height } = useVideoConfig()
  const s = Math.min(width / 1180, height / 1080)
  return (
    <AbsoluteFill style={{ overflow: 'hidden' }}>
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

/** Places a child by its centre, measured from the canvas centre. */
export function At({ x = 0, y = 0, children, style }) {
  return (
    <div style={{ position: 'absolute', left: 960 + x, top: 540 + y, transform: 'translate(-50%, -50%)', ...style }}>
      {children}
    </div>
  )
}

/** One camera per scene: scale and pan around the canvas centre, plus the micro-push. */
export function Camera({ frame, scale = 1, x = 0, y = 0, push = 0.00012, children }) {
  const s = scale * (1 + frame * push)
  return (
    <AbsoluteFill style={{ transform: `translate(${-x * s}px, ${-y * s}px) scale(${s})`, transformOrigin: '960px 540px' }}>
      {children}
    </AbsoluteFill>
  )
}
