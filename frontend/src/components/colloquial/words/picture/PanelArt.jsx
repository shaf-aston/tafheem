/**
 * The grid boards' panels, one small card per spot: positions (a ball and a box), colours,
 * shapes, days, months. Each spot's `area` is where its card sits (lib/colloquial/sceneBoards.js);
 * only a colour panel uses the real colour it names.
 */
import colours from '../../../../lib/colloquial/colourSwatches.json'
import { BALL, LABEL, LINE, SOFT } from './artStyle'

// A box in a position panel: a front, a top and a side, standing on (x, floor).
function Box({ x, floor, w = 36, h = 34 }) {
  const top = floor - h
  return (
    <g stroke="var(--border-hi)" strokeWidth="1.5" strokeLinejoin="round">
      <path d={`M${x} ${top} L${x + 8} ${top - 8} H${x + w + 8} L${x + w} ${top} Z`} fill="var(--surface-hi)" />
      <path d={`M${x + w} ${top} L${x + w + 8} ${top - 8} V${floor - 8} L${x + w} ${floor} Z`} fill="color-mix(in oklab, var(--text-faint) 30%, var(--surface-hi))" />
      <rect x={x} y={top} width={w} height={h} fill="color-mix(in oklab, var(--text-faint) 15%, var(--surface-hi))" />
    </g>
  )
}

// Each position: what to draw in a 120 × 100 panel. The ball is the thing placed.
const POSITION = {
  on: () => <><Box x={42} floor={78} /><circle cx="64" cy="28" r="8" {...BALL} /></>,
  in: () => (
    <>
      <path d="M42 44 L50 36 H86 L78 44 Z" fill="color-mix(in oklab, black 25%, var(--surface-hi))" stroke="var(--border-hi)" strokeWidth="1.5" />
      <circle cx="62" cy="37" r="9" {...BALL} />
      <path d="M78 44 L86 36 V70 L78 78 Z" fill="color-mix(in oklab, var(--text-faint) 30%, var(--surface-hi))" stroke="var(--border-hi)" strokeWidth="1.5" />
      <rect x="42" y="44" width="36" height="34" fill="color-mix(in oklab, var(--text-faint) 15%, var(--surface-hi))" stroke="var(--border-hi)" strokeWidth="1.5" />
    </>
  ),
  under: () => (
    <>
      <path d="M30 40 H90 M36 40 V78 M84 40 V78" {...LINE} strokeWidth="4" />
      <circle cx="60" cy="70" r="8" {...BALL} />
    </>
  ),
  above: () => <><Box x={42} floor={78} /><circle cx="64" cy="14" r="8" {...BALL} /><path d="M64 24 V32" {...LINE} strokeDasharray="2 3" /></>,
  'next-to': () => <><Box x={30} floor={78} /><circle cx="92" cy="70" r="8" {...BALL} /></>,
  behind: () => <><circle cx="86" cy="36" r="10" {...BALL} /><Box x={40} floor={80} w={40} h={38} /></>,
  'in-front-of': () => <><Box x={42} floor={70} /><circle cx="58" cy="72" r="11" {...BALL} /></>,
  between: () => <><Box x={12} floor={78} w={26} h={28} /><Box x={78} floor={78} w={26} h={28} /><circle cx="60" cy="70" r="8" {...BALL} /></>,
  around: () => (
    <>
      <Box x={44} floor={68} w={30} h={28} />
      <ellipse cx="62" cy="54" rx="44" ry="30" fill="none" stroke="var(--border-hi)" strokeDasharray="3 4" />
      {[0, 72, 144, 216, 288].map((deg) => {
        const a = deg * Math.PI / 180
        return <circle key={deg} cx={62 + 44 * Math.cos(a)} cy={54 + 30 * Math.sin(a)} r="5" {...BALL} />
      })}
    </>
  ),
  outside: () => (
    <>
      <rect x="20" y="28" width="56" height="50" rx="4" fill="none" stroke="var(--border-hi)" strokeWidth="3" />
      <circle cx="98" cy="64" r="8" {...BALL} />
    </>
  ),
  opposite: () => (
    <>
      <rect x="48" y="16" width="24" height="76" fill="var(--surface-hi)" />
      <path d="M60 18 V90" stroke="var(--border-hi)" strokeWidth="2" strokeDasharray="6 5" />
      <Box x={8} floor={78} w={28} h={30} />
      <circle cx="96" cy="70" r="8" {...BALL} />
    </>
  ),
  middle: () => (
    <>
      <path d="M14 64 H106 M14 56 V72 M106 56 V72 M60 76 V82" {...LINE} strokeWidth="3" />
      <circle cx="60" cy="54" r="8" {...BALL} />
    </>
  ),
}

const { swatches: COLOUR } = colours

function ColourPanel({ id, w, h }) {
  const c = COLOUR[id]
  const [from, to] = Array.isArray(c) ? c : []
  return (
    <>
      {from && (
        <defs>
          <linearGradient id={`shine-${id}`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor={from} /><stop offset="1" stopColor={to} />
          </linearGradient>
        </defs>
      )}
      <rect x="12" y="10" width={w - 24} height={h - 20} rx="8" fill={from ? `url(#shine-${id})` : c} stroke="var(--border-hi)" strokeWidth="1.5" />
    </>
  )
}

const SHAPE = {
  circle: () => <circle cx="45" cy="40" r="24" {...SOFT} strokeWidth="2.5" />,
  'square-shape': () => <rect x="22" y="17" width="46" height="46" {...SOFT} strokeWidth="2.5" />,
  triangle: () => <path d="M45 14 L70 62 H20 Z" {...SOFT} strokeWidth="2.5" strokeLinejoin="round" />,
  rectangle: () => <rect x="12" y="24" width="66" height="34" {...SOFT} strokeWidth="2.5" />,
  'line-shape': () => <path d="M14 56 L76 24" {...LINE} strokeWidth="4" />,
  point: () => <circle cx="45" cy="40" r="6" fill="var(--text-dim)" />,
  cube: () => (
    <g stroke="var(--border-hi)" strokeWidth="2.5" strokeLinejoin="round">
      <path d="M22 30 L36 16 H70 L56 30 Z" fill="var(--surface-hi)" />
      <path d="M56 30 L70 16 V50 L56 64 Z" fill="color-mix(in oklab, var(--text-faint) 30%, var(--surface-hi))" />
      <rect x="22" y="30" width="34" height="34" fill="color-mix(in oklab, var(--text-faint) 12%, var(--surface-hi))" />
    </g>
  ),
}

const DAY = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTH = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const HIJRI = ['Muharram', 'Safar', 'Rabīʿ I', 'Rabīʿ II', 'Jumādā I', 'Jumādā II', 'Rajab', 'Shaʿbān', 'Ramaḍān', 'Shawwāl', 'Dhū al-Qaʿda', 'Dhū al-Ḥijja']

// A numbered card: the place in the set large, a name under it.
function Numbered({ w, h, n, name, weekend = false, moon = false }) {
  return (
    <>
      <rect x="4" y="4" width={w - 8} height={h - 8} rx="6"
        fill={weekend ? 'color-mix(in oklab, var(--success) 16%, var(--surface))' : 'var(--surface)'} />
      {moon && <path d={`M${w - 20} 12 a7 7 0 1 0 7 10 a5.5 5.5 0 1 1 -7 -10 Z`} fill="var(--warn)" />}
      <text x={w / 2} y={h / 2} fontSize={h > 60 ? 22 : 18} fontWeight="700" {...LABEL} fill="var(--text)">{n}</text>
      <text x={w / 2} y={h - 12} fontSize={name.length > 9 ? 9 : 11} {...LABEL}>{name}</text>
    </>
  )
}

const PANEL = {
  position: ({ id }) => POSITION[id]?.() ?? null,
  colour: ColourPanel,
  shape: ({ id }) => SHAPE[id]?.() ?? null,
  day: ({ order, w, h }) => <Numbered w={w} h={h} n={order} name={DAY[order - 1]} weekend={order >= 6} />,
  month: ({ order, w, h }) => <Numbered w={w} h={h} n={order} name={MONTH[order - 1]} />,
  hijri: ({ order, w, h }) => <Numbered w={w} h={h} n={order} name={HIJRI[order - 1]} moon={order === 9} />,
}

// Nothing for a board that is not a grid.
export default function PanelArt({ board }) {
  const Panel = PANEL[board.art]
  if (!Panel) return null
  return board.spots.map(({ key, area: [x, y, w, h], order }) => (
    <g key={key} transform={`translate(${x} ${y})`}>
      <rect x="2" y="2" width={w - 4} height={h - 4} rx="8" fill="var(--surface)" stroke="var(--border)" strokeWidth="1" />
      <Panel id={key} order={order} w={w} h={h} />
    </g>
  ))
}
