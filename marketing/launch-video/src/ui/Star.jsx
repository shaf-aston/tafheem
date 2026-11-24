// The eight-point star (two squares turned 45° apart), the geometric motif the
// landing page already turns behind its story. Drawn as one outline path.
export function starPath(r, inner = 0.76) {
  const pts = []
  for (let i = 0; i < 16; i++) {
    const a = (Math.PI / 8) * i - Math.PI / 2
    const rad = i % 2 === 0 ? r : r * inner
    pts.push(`${(Math.cos(a) * rad).toFixed(2)},${(Math.sin(a) * rad).toFixed(2)}`)
  }
  return `M${pts.join('L')}Z`
}

export function Star({ r, stroke, fill = 'none', width = 1.5, inner, dash, offset, opacity = 1 }) {
  return (
    <path
      d={starPath(r, inner)}
      fill={fill}
      stroke={stroke}
      strokeWidth={width}
      strokeLinejoin="round"
      strokeDasharray={dash}
      strokeDashoffset={offset}
      opacity={opacity}
    />
  )
}
