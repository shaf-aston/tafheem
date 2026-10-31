/**
 * The body drawings behind WordPicture's spots: a face, a whole figure with its
 * organs showing through, and an open hand. Plain shapes in theme colours, so
 * they read in light and dark. The spots' places are lib/colloquial/wordPictures.js,
 * drawn to the same viewBox; move a part here and move its spot there.
 */
const SKIN = { fill: 'var(--surface-hi)', stroke: 'var(--border-hi)', strokeWidth: 2 }
const LINE = { fill: 'none', stroke: 'var(--text-faint)', strokeWidth: 2.5, strokeLinecap: 'round' }
const ORGAN = (pct) => ({ fill: `color-mix(in oklab, var(--danger) ${pct}%, var(--surface-hi))`, stroke: 'var(--border-hi)', strokeWidth: 1 })

function Face() {
  return (
    <g>
      <path d="M96 226 L96 260 Q58 270 26 300 L214 300 Q182 270 144 260 L144 226 Z" {...SKIN} />
      <ellipse cx="40" cy="142" rx="12" ry="22" {...SKIN} />
      <ellipse cx="200" cy="142" rx="12" ry="22" {...SKIN} />
      <ellipse cx="120" cy="134" rx="78" ry="104" {...SKIN} />
      <path d="M60 176 Q66 232 120 240 Q174 232 180 176 Q172 206 150 214 Q120 228 90 214 Q68 206 60 176 Z" fill="var(--text-faint)" opacity=".35" />
      <path d="M42 134 Q36 34 120 26 Q204 34 198 134 Q196 86 172 66 Q120 50 68 66 Q44 86 42 134 Z" fill="var(--text-faint)" />
      <path d="M70 102 Q88 92 106 102 M134 102 Q152 92 170 102" {...LINE} strokeWidth="4" />
      {[88, 152].map((cx) => (
        <g key={cx}>
          <ellipse cx={cx} cy="120" rx="14" ry="7" fill="var(--surface)" stroke="var(--text-faint)" strokeWidth="1.5" />
          <circle cx={cx} cy="120" r="4" fill="var(--text)" />
        </g>
      ))}
      <path d="M120 118 L110 160 Q120 167 130 160" {...LINE} />
      <circle cx="72" cy="166" r="13" {...ORGAN(25)} stroke="none" />
      <circle cx="168" cy="166" r="13" {...ORGAN(25)} stroke="none" />
      <path d="M84 186 Q120 236 156 186 Q120 194 84 186 Z" fill="var(--text)" opacity=".75" />
      <rect x="102" y="186" width="36" height="7" rx="2" fill="var(--surface)" />
      <ellipse cx="120" cy="206" rx="14" ry="6" {...ORGAN(55)} />
      <path d="M84 186 Q102 178 120 183 Q138 178 156 186" {...LINE} stroke={ORGAN(60).fill} strokeWidth="4" />
      <path d="M84 186 Q120 240 156 186" {...LINE} stroke={ORGAN(60).fill} strokeWidth="5" />
    </g>
  )
}

function Figure() {
  return (
    <g>
      {/* Limbs as thick strokes: an outline pass under a skin pass, so they read as shapes. */}
      {[['var(--border-hi)', 4], ['var(--surface-hi)', 0]].map(([stroke, extra]) => (
        <g key={stroke} {...LINE} stroke={stroke}>
          <path d="M74 92 L58 160 L50 226 M166 92 L182 160 L190 226" strokeWidth={18 + extra} />
          <path d="M104 206 L98 292 L95 366 M136 206 L142 292 L145 366" strokeWidth={24 + extra} />
          <path d="M95 374 L72 386 M145 374 L168 386" strokeWidth={12 + extra} />
        </g>
      ))}
      <circle cx="48" cy="240" r="11" {...SKIN} />
      <circle cx="192" cy="240" r="11" {...SKIN} />
      <rect x="112" y="62" width="16" height="16" {...SKIN} />
      <path d="M72 84 Q120 72 168 84 L162 212 Q120 222 78 212 Z" {...SKIN} />
      <circle cx="120" cy="38" r="27" {...SKIN} />
      <ellipse cx="122" cy="31" rx="17" ry="11" {...ORGAN(30)} />
      <ellipse cx="99" cy="124" rx="14" ry="26" {...ORGAN(25)} />
      <ellipse cx="141" cy="124" rx="14" ry="26" {...ORGAN(25)} />
      <path d="M131 124 Q124 116 124 128 Q124 136 131 144 Q138 136 138 128 Q138 116 131 124 Z" {...ORGAN(75)} />
      <ellipse cx="106" cy="162" rx="20" ry="11" {...ORGAN(45)} />
      <ellipse cx="140" cy="166" rx="14" ry="11" {...ORGAN(35)} />
      <ellipse cx="101" cy="194" rx="6" ry="10" {...ORGAN(55)} />
      <ellipse cx="139" cy="194" rx="6" ry="10" {...ORGAN(55)} />
    </g>
  )
}

function Hand() {
  const fingers = [[62, 54], [90, 32], [118, 28], [146, 58]]
  return (
    <g>
      <rect x="82" y="224" width="68" height="76" {...SKIN} />
      <path d="M66 176 Q46 168 30 132 Q24 118 36 114 Q48 112 58 128 L72 148 Z" {...SKIN} />
      {fingers.map(([x, y]) => (
        <g key={x}>
          <rect x={x} y={y} width="26" height={150 - y} rx="13" {...SKIN} />
          <rect x={x + 5} y={y + 4} width="16" height="14" rx="6" fill="var(--surface)" stroke="var(--border-hi)" strokeWidth="1" />
        </g>
      ))}
      <rect x="58" y="120" width="118" height="116" rx="34" {...SKIN} />
      <path d="M78 160 Q116 150 154 168 M84 194 Q112 206 150 192" {...LINE} strokeWidth="1.5" opacity=".6" />
    </g>
  )
}

const ART = { face: Face, figure: Figure, hand: Hand }

export default function BodyArt({ art }) {
  const Art = ART[art]
  return Art ? <Art /> : null
}
