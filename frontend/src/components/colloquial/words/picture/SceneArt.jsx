/**
 * The everyday drawings behind WordPicture's spots: a family tree, a house, a
 * crossroads, a compass, a clock and the weather. The grid boards' panels (positions,
 * colours, shapes, days, months) are PanelArt.jsx. Plain shapes in theme colours so
 * they read in light and dark.
 * The spots' places are lib/colloquial/sceneBoards.js, drawn to the same viewBox;
 * move a part here and move its spot there.
 */
import { FAINT, LABEL, LINE, SOFT } from './artStyle'


// ── Family ─────────────────────────────────────────────────────────────────────

// A person: shoulders under a head; a woman wears a scarf. The head is where the
// spot's dot sits, so the dot becomes the face and the scarf shows round it.
function Person({ x, y, woman = false, ghost = false }) {
  return (
    <g opacity={ghost ? 0.35 : 1}>
      {woman && <path d={`M${x - 13} ${y + 2} Q${x - 14} ${y - 15} ${x} ${y - 15} Q${x + 14} ${y - 15} ${x + 13} ${y + 2} L${x + 17} ${y + 24} L${x - 17} ${y + 24} Z`} fill="var(--text-faint)" opacity=".55" />}
      <path d={`M${x - 15} ${y + 26} Q${x - 15} ${y + 11} ${x} ${y + 11} Q${x + 15} ${y + 11} ${x + 15} ${y + 26} Z`} {...SOFT} />
      <circle cx={x} cy={y} r="10" {...SOFT} />
    </g>
  )
}

// Children hang from a bar under their parents' line: [drop x, from y, bar y, child xs, child y].
const kin = (x, from, bar, children, to) =>
  `M${x} ${from} V${bar} M${Math.min(...children, x)} ${bar} H${Math.max(...children, x)} ${children.map((c) => `M${c} ${bar} V${to}`).join(' ')}`

function Family() {
  const W = true
  const people = [
    [70, 30], [125, 30, W], [235, 30, false, true], [290, 30, W, true],
    [25, 115], [75, 115, W], [130, 115], [230, 115, W], [285, 115], [335, 115, W],
    [25, 200], [80, 200], [125, 200, W], [180, 200], [225, 200, W], [285, 200, W], [335, 200],
    [180, 285], [225, 285, W], [285, 285], [335, 285, W],
    [160, 365], [205, 365, W],
  ]
  return (
    <g>
      <g {...LINE}>
        {/* Couples joined side by side; children below. */}
        <path d="M82 30 H113 M247 30 H278 M142 115 H218 M92 200 H113 M192 200 H213 M297 200 H323" />
        <path d={kin(97, 30, 72, [25, 75, 130], 103)} />
        <path d={kin(262, 30, 72, [230, 285, 335], 103)} />
        <path d={kin(180, 115, 157, [80, 180, 285], 188)} />
        <path d="M25 141 V188" />
        <path d={kin(202, 200, 242, [180, 225], 273)} />
        <path d={kin(310, 200, 242, [285, 335], 273)} />
        <path d={kin(180, 311, 331, [160, 205], 353)} />
      </g>
      {people.map(([x, y, woman, ghost]) => <Person key={`${x}-${y}`} x={x} y={y} woman={woman} ghost={ghost} />)}
      {/* You: ringed, and named, so every other word is read from here. */}
      <circle cx="180" cy="200" r="15" fill="none" stroke="var(--primary)" strokeWidth="2.5" strokeDasharray="4 3" />
      <text x="180" y="200" dy="4" fontSize="10" fontWeight="700" {...LABEL} fill="var(--primary)">you</text>
    </g>
  )
}

// ── House ──────────────────────────────────────────────────────────────────────

function House() {
  return (
    <g>
      {/* Garden, ground and a tree. */}
      <rect x="0" y="280" width="360" height="20" fill="color-mix(in oklab, var(--success) 25%, var(--surface))" />
      <rect x="0" y="200" width="56" height="80" fill="color-mix(in oklab, var(--success) 14%, var(--surface))" rx="6" />
      <rect x="24" y="236" width="8" height="44" fill="color-mix(in oklab, var(--warn) 40%, var(--text-faint))" />
      <circle cx="28" cy="226" r="20" fill="color-mix(in oklab, var(--success) 55%, var(--surface-hi))" />
      {/* Roof, walls, floors and the inside walls. */}
      <path d="M48 100 L180 32 L312 100 Z" fill="color-mix(in oklab, var(--danger) 30%, var(--surface-hi))" stroke="var(--border-hi)" strokeWidth="2" />
      <rect x="60" y="100" width="240" height="180" fill="var(--surface)" stroke="var(--border-hi)" strokeWidth="2.5" />
      <path d="M60 190 H300 M170 100 V190 M230 100 V190 M140 190 V280 M180 190 V280" {...LINE} />
      {/* Balcony off the top floor. */}
      <path d="M300 190 H348 M300 160 H348 M348 160 V190 M312 160 V190 M324 160 V190 M336 160 V190" {...LINE} strokeWidth="1.5" />
      {/* Stairs. */}
      <path d="M142 278 H150 V262 H158 V246 H166 V230 H174 V214 H180" {...LINE} strokeWidth="1.5" />
      {/* Bedroom: wardrobe, bed, window. */}
      <rect x="66" y="126" width="22" height="64" {...SOFT} />
      <path d="M77 130 V186" {...LINE} strokeWidth="1" />
      <rect x="96" y="168" width="68" height="20" rx="3" {...SOFT} />
      <rect x="98" y="160" width="16" height="10" rx="3" {...SOFT} />
      <rect x="126" y="112" width="28" height="26" fill="color-mix(in oklab, var(--primary) 18%, var(--surface))" stroke="var(--border-hi)" strokeWidth="1.5" />
      <path d="M140 112 V138 M126 125 H154" {...LINE} strokeWidth="1" />
      {/* Bathroom: mirror and bath. */}
      <ellipse cx="200" cy="125" rx="11" ry="13" fill="color-mix(in oklab, var(--primary) 12%, var(--surface))" stroke="var(--border-hi)" strokeWidth="1.5" />
      <path d="M176 170 H224 V182 Q224 190 214 190 H186 Q176 190 176 182 Z" {...SOFT} />
      {/* Guest room: a table and a chair. */}
      <path d="M240 164 H272 M244 164 V190 M268 164 V190" {...LINE} strokeWidth="3" />
      <path d="M282 146 V190 M282 172 H294 V190" {...LINE} strokeWidth="3" />
      {/* Kitchen: cupboard, fridge, cooker. */}
      <rect x="94" y="200" width="36" height="18" {...SOFT} />
      <rect x="66" y="212" width="22" height="66" rx="2" {...SOFT} />
      <path d="M66 236 H88" {...LINE} strokeWidth="1" />
      <rect x="96" y="250" width="30" height="28" {...SOFT} />
      <path d="M100 254 H122" stroke="var(--danger)" strokeWidth="2" />
      {/* Living room: a hanging light, a window with curtains, a sofa, the front door. */}
      <path d="M210 190 V200" {...LINE} strokeWidth="1" />
      <path d="M202 206 Q210 196 218 206 Z" fill="color-mix(in oklab, var(--warn) 55%, var(--surface-hi))" />
      <rect x="238" y="202" width="26" height="22" fill="color-mix(in oklab, var(--primary) 18%, var(--surface))" stroke="var(--border-hi)" strokeWidth="1.5" />
      <path d="M236 200 Q240 214 236 228 L242 228 Q244 214 242 200 Z M266 200 Q262 214 266 228 L260 228 Q258 214 260 200 Z" fill="color-mix(in oklab, var(--danger) 45%, var(--surface-hi))" />
      <path d="M190 278 V256 Q190 250 196 250 H236 Q242 250 242 256 V278 Z" fill="color-mix(in oklab, var(--primary) 30%, var(--surface-hi))" stroke="var(--border-hi)" strokeWidth="1.5" />
      <rect x="270" y="222" width="22" height="56" rx="1" fill="color-mix(in oklab, var(--warn) 30%, var(--surface-hi))" stroke="var(--border-hi)" strokeWidth="1.5" />
      <circle cx="287" cy="252" r="1.8" {...FAINT} />
    </g>
  )
}

// ── Crossroads ─────────────────────────────────────────────────────────────────

function Crossroads() {
  const arrow = { ...LINE, stroke: 'var(--primary)', strokeWidth: 5 }
  return (
    <g>
      <rect x="0" y="0" width="300" height="300" fill="color-mix(in oklab, var(--success) 10%, var(--surface))" />
      <path d="M120 0 V300 M180 0 V300" stroke="none" />
      <rect x="118" y="0" width="64" height="300" fill="var(--surface-hi)" />
      <rect x="0" y="118" width="300" height="64" fill="var(--surface-hi)" />
      <path d="M150 0 V112 M150 188 V300 M0 150 H112 M188 150 H300" stroke="var(--border-hi)" strokeWidth="2" strokeDasharray="10 8" />
      {/* Corners of the blocks, and what stands on them. */}
      <path d="M118 0 V118 H0 M182 0 V118 H300 M118 300 V182 H0 M182 300 V182 H300" {...LINE} />
      {/* A masjid: a dome and a minaret. */}
      <rect x="40" y="62" width="44" height="30" {...SOFT} />
      <path d="M44 62 Q62 34 80 62 Z" {...SOFT} />
      <rect x="88" y="34" width="10" height="58" {...SOFT} />
      <path d="M88 34 L93 24 L98 34" {...SOFT} />
      {/* A pharmacy: a green cross over its door. */}
      <rect x="216" y="44" width="50" height="48" {...SOFT} />
      <path d="M236 50 h10 v10 h10 v10 h-10 v10 h-10 v-10 h-10 v-10 h10 Z" fill="var(--success)" />
      {/* A traffic light and a road sign. */}
      <rect x="191" y="72" width="14" height="36" rx="3" fill="var(--text-faint)" />
      {['var(--danger)', 'var(--warn)', 'var(--success)'].map((fill, i) => <circle key={fill} cx="198" cy={79 + i * 11} r="4" fill={fill} />)}
      <path d="M212 236 V270" {...LINE} strokeWidth="3" />
      <path d="M212 206 L230 236 H194 Z" fill="var(--surface)" stroke="var(--danger)" strokeWidth="3" strokeLinejoin="round" />
      {/* You, walking up from the bottom; the ways you can go. */}
      <path d="M150 270 V60 M141 70 L150 54 L159 70" {...arrow} />
      <path d="M150 196 Q150 150 104 150 H56 M66 141 L50 150 L66 159" {...arrow} />
      <path d="M150 196 Q150 150 196 150 H244 M234 141 L250 150 L234 159" {...arrow} />
      <circle cx="150" cy="282" r="9" fill="var(--primary)" />
    </g>
  )
}

// ── Compass ────────────────────────────────────────────────────────────────────

function Compass() {
  const points = [['N', 150, 22], ['E', 280, 155], ['S', 150, 290], ['W', 20, 155]]
  return (
    <g>
      <circle cx="150" cy="150" r="118" {...SOFT} strokeWidth="2" />
      <circle cx="150" cy="150" r="96" fill="none" stroke="var(--border)" strokeWidth="1" />
      <path d="M150 54 L168 132 L246 150 L168 168 L150 246 L132 168 L54 150 L132 132 Z" fill="color-mix(in oklab, var(--primary) 18%, var(--surface))" stroke="var(--border-hi)" strokeWidth="1.5" />
      <path d="M150 54 L168 132 L150 150 Z M246 150 L168 168 L150 150 Z M150 246 L132 168 L150 150 Z M54 150 L132 132 L150 150 Z" fill="color-mix(in oklab, var(--primary) 40%, var(--surface-hi))" />
      <circle cx="150" cy="150" r="5" {...FAINT} />
      {points.map(([letter, x, y]) => <text key={letter} x={x} y={y} fontSize="16" fontWeight="700" {...LABEL}>{letter}</text>)}
    </g>
  )
}

// ── Clock ──────────────────────────────────────────────────────────────────────

const EASTERN = '٠١٢٣٤٥٦٧٨٩'
const eastern = (n) => String(n).split('').map((d) => EASTERN[d]).join('')

function Clock() {
  const at = (hour, r) => {
    const a = (hour % 12) * Math.PI / 6
    return [150 + r * Math.sin(a), 150 - r * Math.cos(a)]
  }
  const hours = Array.from({ length: 12 }, (_, i) => i + 1)
  return (
    <g>
      <circle cx="150" cy="150" r="140" {...SOFT} strokeWidth="2.5" />
      {Array.from({ length: 60 }, (_, m) => {
        const [x1, y1] = at(m / 5, 134)
        const [x2, y2] = at(m / 5, m % 5 ? 130 : 126)
        return <path key={m} d={`M${x1} ${y1} L${x2} ${y2}`} stroke="var(--border-hi)" strokeWidth={m % 5 ? 1 : 2} />
      })}
      {hours.map((h) => {
        const [x, y] = at(h, 100)
        const [ex, ey] = at(h, 76)
        return (
          <g key={h}>
            <text x={x} y={y} dy="6" fontSize="18" fontWeight="600" {...LABEL} fill="var(--text)">{h}</text>
            <text x={ex} y={ey} dy="4" fontSize="12" {...LABEL} fill="var(--text-faint)">{eastern(h)}</text>
          </g>
        )
      })}
      <path d="M150 150 L189 189" {...LINE} stroke="var(--text-dim)" strokeWidth="7" />
      <path d="M150 150 L150 70" {...LINE} stroke="var(--text-dim)" strokeWidth="4" />
      <circle cx="150" cy="150" r="6" fill="var(--text-dim)" />
    </g>
  )
}

// ── Weather ────────────────────────────────────────────────────────────────────

const cloud = (x, y, s = 1) =>
  `M${x - 34 * s} ${y + 12 * s} Q${x - 46 * s} ${y + 12 * s} ${x - 44 * s} ${y} Q${x - 42 * s} ${y - 12 * s} ${x - 28 * s} ${y - 10 * s} Q${x - 22 * s} ${y - 28 * s} ${x} ${y - 24 * s} Q${x + 18 * s} ${y - 30 * s} ${x + 26 * s} ${y - 12 * s} Q${x + 44 * s} ${y - 12 * s} ${x + 44 * s} ${y + 2 * s} Q${x + 44 * s} ${y + 12 * s} ${x + 32 * s} ${y + 12 * s} Z`

function Weather() {
  const sun = 'color-mix(in oklab, var(--warn) 75%, var(--surface-hi))'
  return (
    <g>
      <rect x="0" y="0" width="360" height="260" rx="10" fill="color-mix(in oklab, var(--primary) 8%, var(--surface))" />
      <rect x="0" y="226" width="360" height="34" fill="color-mix(in oklab, var(--success) 22%, var(--surface))" />
      {/* Sun. */}
      {Array.from({ length: 8 }, (_, i) => {
        const a = i * Math.PI / 4
        return <path key={i} d={`M${70 + 34 * Math.cos(a)} ${62 + 34 * Math.sin(a)} L${70 + 46 * Math.cos(a)} ${62 + 46 * Math.sin(a)}`} stroke={sun} strokeWidth="4" strokeLinecap="round" />
      })}
      <circle cx="70" cy="62" r="26" fill={sun} />
      {/* A white cloud; a dark one with rain and lightning. */}
      <path d={cloud(190, 52)} fill="var(--surface-hi)" stroke="var(--border-hi)" strokeWidth="1.5" />
      <path d={cloud(300, 66)} fill="color-mix(in oklab, var(--text-faint) 55%, var(--surface-hi))" stroke="var(--border-hi)" strokeWidth="1.5" />
      <path d="M268 92 l-6 16 M284 96 l-6 16 M300 92 l-6 16 M276 116 l-6 16 M292 120 l-6 16 M308 114 l-6 16" stroke="var(--primary)" strokeWidth="3" strokeLinecap="round" />
      <path d="M332 92 L320 120 H332 L322 146 L344 112 H332 L340 92 Z" fill="var(--warn)" />
      {/* Snowflake. */}
      <g stroke="var(--primary)" strokeWidth="2.5" strokeLinecap="round">
        {[0, 60, 120].map((deg) => <path key={deg} d="M180 132 V168 M174 138 L180 144 L186 138 M174 162 L180 156 L186 162" transform={`rotate(${deg} 180 150)`} />)}
      </g>
      {/* Wind. */}
      <path d="M58 146 H110 Q122 146 122 136 Q122 126 112 128 M58 162 H126 Q140 162 140 174 Q140 184 128 182 M66 178 H100" {...LINE} stroke="var(--text-faint)" strokeWidth="3" />
      {/* Someone under an umbrella. */}
      <path d="M222 178 Q256 140 290 178 Q281 172 273 178 Q264 172 256 178 Q248 172 239 178 Q231 172 222 178 Z" fill="var(--danger)" />
      <path d="M256 178 V216 Q256 222 250 220" {...LINE} stroke="var(--text-dim)" />
      <circle cx="246" cy="192" r="7" {...SOFT} />
      <path d="M236 226 Q236 202 246 202 Q256 202 256 226 Z" {...SOFT} />
      {/* A thermometer: hot at the top, cold at the bottom. */}
      <rect x="22" y="150" width="16" height="96" rx="8" {...SOFT} />
      <rect x="25" y="152" width="10" height="46" rx="5" fill="var(--danger)" />
      <rect x="25" y="200" width="10" height="44" rx="5" fill="var(--primary)" />
    </g>
  )
}

const SCENE = { family: Family, house: House, crossroads: Crossroads, compass: Compass, clock: Clock, weather: Weather }

// Nothing for a board it does not draw (a body, a map, a grid).
export default function SceneArt({ board }) {
  const Scene = SCENE[board.art]
  return Scene ? <Scene /> : null
}
