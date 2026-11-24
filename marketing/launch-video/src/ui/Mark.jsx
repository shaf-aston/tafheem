import { C } from '../config'

// Tafheem's mark from frontend/public/favicon.svg: an open book, the left panel an
// outline and the right one solid gold, the spine left open between them.
// draw (0..1) traces the outline, fill (0..1) pours the gold.
const LEFT = 'M5 6.8 h6.4 v10.8 l-3.2 -1.7 -3.2 1.7 z'
const RIGHT = 'M12.6 6.8 h6.4 v10.8 l-3.2 -1.7 -3.2 1.7 z'

export function Mark({ size = 120, draw = 1, fill = 1, line = C.text, gold = C.goldHi, plate }) {
  return (
    <svg width={size} height={size} viewBox="3 4 18 16">
      {plate && <rect x="3" y="4" width="18" height="16" rx="4" fill={plate} />}
      <path d={LEFT} pathLength="1" fill="none" stroke={line} strokeWidth="1.3" strokeLinejoin="round" strokeDasharray="1" strokeDashoffset={1 - draw} />
      <path d={RIGHT} pathLength="1" fill={gold} fillOpacity={fill} stroke={gold} strokeWidth="1.3" strokeLinejoin="round" strokeDasharray="1" strokeDashoffset={1 - draw} />
    </svg>
  )
}
