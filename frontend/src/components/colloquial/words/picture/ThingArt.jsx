/**
 * The drawings of things behind WordPicture's spots, beside the body (BodyArt.jsx) and the
 * everyday scenes (SceneArt.jsx): a figure in a full outfit, three in the clothes of the
 * region, a laid table and a plant with its roots. Plain shapes in theme colours so they read
 * in light and dark. The spots' places are lib/colloquial/sceneBoards.js, drawn to the same
 * viewBox; move a part here and move its spot there.
 */
const SKIN = { fill: 'var(--surface-hi)', stroke: 'var(--border-hi)', strokeWidth: 2 }
const mix = (token, pct, base = 'var(--surface-hi)') => `color-mix(in oklab, var(${token}) ${pct}%, ${base})`
const EDGE = { stroke: 'var(--border-hi)', strokeWidth: 1.5, strokeLinejoin: 'round', strokeLinecap: 'round' }
const CLOTH = (token, pct = 55) => ({ fill: mix(token, pct), ...EDGE })
const WHITE = 'color-mix(in oklab, white 90%, var(--surface-hi))'
const BLACK = 'color-mix(in oklab, black 78%, var(--surface-hi))'
const STROKE = (c, w) => ({ fill: 'none', stroke: c, strokeWidth: w, strokeLinecap: 'round', strokeLinejoin: 'round' })

// ── Clothes: one figure wearing a little of everything ─────────────────────────

function Outfit() {
  const jacket = mix('--primary', 62)
  const trousers = mix('--text-faint', 70)
  return (
    <g>
      {/* Legs and socks and shoes. */}
      <path d="M122 236 L120 330 L118 388 M158 236 L160 330 L162 388" {...STROKE('var(--border-hi)', 34)} />
      <path d="M122 236 L120 330 L118 388 M158 236 L160 330 L162 388" {...STROKE(trousers, 30)} />
      <path d="M118 372 V396 M162 372 V396" {...STROKE(WHITE, 22)} />
      <path d="M96 408 Q98 394 116 396 L134 404 Q136 418 118 420 L100 420 Z" fill={BLACK} {...EDGE} />
      <path d="M184 408 Q182 394 164 396 L146 404 Q144 418 162 420 L180 420 Z" fill={BLACK} {...EDGE} />
      {/* Hands, then sleeves over them. */}
      <circle cx="70" cy="256" r="12" {...SKIN} />
      <circle cx="210" cy="256" r="12" {...SKIN} />
      <path d="M92 108 L74 190 L70 238 M188 108 L206 190 L210 238" {...STROKE('var(--border-hi)', 26)} />
      <path d="M92 108 L74 190 L70 238 M188 108 L206 190 L210 238" {...STROKE(jacket, 22)} />
      {/* The glove on the left hand, the watch on the right wrist. */}
      <path d="M60 250 Q58 238 70 238 Q82 238 80 250 L82 266 Q70 274 58 266 Z" fill={mix('--warn', 70)} {...EDGE} />
      <rect x="198" y="230" width="24" height="9" rx="3" fill={BLACK} />
      <circle cx="210" cy="234.5" r="6" fill={WHITE} stroke={BLACK} strokeWidth="2" />
      {/* Torso: shirt in the middle, the jacket open either side. */}
      <path d="M92 104 Q140 94 188 104 L184 238 Q140 246 96 238 Z" {...SKIN} />
      <path d="M124 100 L156 100 L152 238 L128 238 Z" fill={WHITE} {...EDGE} />
      <path d="M92 104 Q112 98 126 100 L128 238 Q112 240 96 238 Z" fill={jacket} {...EDGE} />
      <path d="M188 104 Q168 98 154 100 L152 238 Q168 240 184 238 Z" fill={jacket} {...EDGE} />
      <rect x="96" y="196" width="26" height="22" rx="3" fill="none" stroke="var(--border-hi)" strokeWidth="1.5" />
      <path d="M96 196 H122" {...STROKE('var(--border-hi)', 3)} />
      {/* Shirt buttons, collar and a tie. */}
      <circle cx="140" cy="204" r="2.6" fill="var(--text-faint)" />
      <circle cx="140" cy="224" r="2.6" fill="var(--text-faint)" />
      <path d="M140 104 L131 114 L140 176 L149 114 Z" fill={mix('--danger', 70)} {...EDGE} />
      <path d="M124 94 L142 112 L130 106 Z M156 94 L138 112 L150 106 Z" fill={WHITE} {...EDGE} />
      {/* A scarf's tail on the chest. */}
      <path d="M154 112 Q176 112 178 134 L176 168 L160 168 L162 134 Q160 124 154 122 Z" fill={mix('--warn', 75)} {...EDGE} />
      {/* A belt, then the bag on the right hand. */}
      <rect x="96" y="232" width="88" height="10" fill={BLACK} />
      <rect x="132" y="231" width="16" height="12" rx="2" fill="none" stroke={WHITE} strokeWidth="2" />
      <path d="M212 266 Q212 284 226 284 M208 266 Q208 284 194 284" {...STROKE(BLACK, 3)} />
      <rect x="186" y="280" width="48" height="36" rx="6" fill={mix('--danger', 45)} {...EDGE} />
      {/* The head: ear, face, glasses, hat. */}
      <rect x="130" y="82" width="20" height="18" {...SKIN} />
      <ellipse cx="112" cy="62" rx="5" ry="9" {...SKIN} />
      <circle cx="112" cy="73" r="3.2" fill={mix('--warn', 90)} />
      <circle cx="140" cy="58" r="27" {...SKIN} />
      <circle cx="129" cy="60" r="9" {...STROKE(BLACK, 2.5)} fill={mix('--primary', 12, 'transparent')} />
      <circle cx="151" cy="60" r="9" {...STROKE(BLACK, 2.5)} fill={mix('--primary', 12, 'transparent')} />
      <path d="M138 60 H142" {...STROKE(BLACK, 2.5)} />
      <path d="M130 76 Q140 82 150 76" {...STROKE('var(--text-faint)', 2)} />
      <ellipse cx="140" cy="38" rx="44" ry="8" fill={mix('--warn', 55)} {...EDGE} />
      <path d="M110 38 Q110 12 140 12 Q170 12 170 38 Z" fill={mix('--warn', 55)} {...EDGE} />
      <path d="M110 34 H170" {...STROKE(BLACK, 4)} />
    </g>
  )
}

// ── Traditional dress: three figures of the region ─────────────────────────────

// One standing figure in a long garment: head and a headcloth, then the garment to the floor.
function Robed({ x, garment, cloth, headcloth, hands = true }) {
  return (
    <g transform={`translate(${x} 0)`}>
      <path d="M-34 100 Q0 86 34 100 L46 360 Q0 372 -46 360 Z" fill={garment} {...EDGE} />
      <path d="M-14 100 Q0 114 14 100" {...STROKE('var(--border-hi)', 2)} />
      {hands && <><circle cx="-44" cy="236" r="9" {...SKIN} /><circle cx="44" cy="236" r="9" {...SKIN} /></>}
      <path d="M-34 104 L-44 230 M34 104 L44 230" {...STROKE(garment, 16)} />
      <ellipse cx="-16" cy="364" rx="14" ry="6" fill={BLACK} /><ellipse cx="16" cy="364" rx="14" ry="6" fill={BLACK} />
      <circle cx="0" cy="62" r="25" {...SKIN} />
      {headcloth}
      {cloth}
    </g>
  )
}

function Traditional() {
  const woman = (
    // A headscarf framing the face, and the veil down over the shoulders.
    <path d="M-30 70 Q-32 28 0 28 Q32 28 30 70 L38 112 Q0 98 -38 112 Z M-17 70 Q-17 46 0 46 Q17 46 17 70 Q17 82 0 84 Q-17 82 -17 70 Z" fill={BLACK} fillRule="evenodd" {...EDGE} />
  )
  const checked = (
    // The keffiyeh: a checked cloth over the head, falling at the sides, held by a black cord.
    <g>
      <path d="M-30 66 Q-30 28 0 28 Q30 28 30 66 L34 96 L22 90 L22 66 Q22 46 0 46 Q-22 46 -22 66 L-22 90 L-34 96 Z" fill={WHITE} {...EDGE} />
      <path d="M-24 36 H24 M-29 46 H-21 M21 46 H29 M-30 66 H-23 M23 66 H30 M-33 82 H-23 M23 82 H33" {...STROKE('var(--danger)', 2.5)} strokeDasharray="4 3" />
      <path d="M-27 40 Q0 28 27 40" {...STROKE(BLACK, 5)} />
    </g>
  )
  const turban = (
    <g>
      <path d="M-27 52 Q-26 22 0 20 Q26 22 27 52 Q0 42 -27 52 Z" fill={WHITE} {...EDGE} />
      <path d="M-26 44 Q0 34 26 44 M-24 34 Q0 24 24 34" {...STROKE('var(--border-hi)', 2)} />
    </g>
  )
  return (
    <g>
      <Robed x={62} garment={WHITE} headcloth={checked} />
      <Robed x={180} garment={BLACK} headcloth={woman} hands={false} />
      <Robed x={298} garment={mix('--text-faint', 55)} headcloth={turban} />
      {/* A man's robe over the garment: open at the front, with a border. */}
      <path d="M298 104 L298 362" {...STROKE('var(--border-hi)', 2)} />
      <path d="M276 108 L282 360 M320 108 L314 360" {...STROKE(mix('--warn', 70), 5)} />
    </g>
  )
}

// ── A laid table, from above ───────────────────────────────────────────────────

function Table() {
  const metal = mix('--text-faint', 35)
  return (
    <g>
      <rect x="6" y="6" width="288" height="288" rx="14" fill={mix('--primary', 14, 'var(--surface)')} {...EDGE} />
      <path d="M6 26 H294 M6 274 H294" {...STROKE(mix('--primary', 35, 'var(--surface)'), 3)} strokeDasharray="10 6" />
      {/* A napkin, then the fork on the left and the knife and spoon on the right. */}
      <path d="M44 74 H78 V130 H44 Z" fill={WHITE} {...EDGE} />
      <path d="M44 86 H78 M44 98 H78" {...STROKE('var(--border-hi)', 1)} />
      <g {...STROKE(metal, 4)}>
        <path d="M96 100 V166 M88 100 V122 M104 100 V122 M88 122 Q96 130 104 122" />
      </g>
      <path d="M200 100 Q210 104 210 132 V168" {...STROKE(metal, 4)} />
      <ellipse cx="226" cy="116" rx="9" ry="14" fill={metal} {...EDGE} />
      <path d="M226 130 V168" {...STROKE(metal, 4)} />
      {/* The plate, with a bowl on it. */}
      <circle cx="150" cy="130" r="48" fill={WHITE} {...EDGE} />
      <circle cx="150" cy="130" r="34" fill="none" stroke="var(--border)" strokeWidth="1.5" />
      {/* A bowl, on the right. */}
      <circle cx="262" cy="180" r="24" fill={mix('--danger', 22)} {...EDGE} />
      <circle cx="262" cy="180" r="15" fill={mix('--warn', 50)} {...EDGE} />
      {/* A glass, a cup on its saucer with its teaspoon, a teapot and the salt. */}
      <circle cx="238" cy="60" r="17" fill={mix('--primary', 18, 'transparent')} stroke="var(--primary)" strokeWidth="2" />
      <circle cx="238" cy="60" r="11" fill="none" stroke="var(--primary)" strokeWidth="1" opacity=".6" />
      <circle cx="58" cy="206" r="26" fill={WHITE} {...EDGE} />
      <circle cx="58" cy="206" r="15" fill={mix('--danger', 45)} {...EDGE} />
      <path d="M73 206 Q86 206 84 218" {...STROKE(BLACK, 3)} />
      <path d="M92 250 L120 218" {...STROKE(metal, 3.5)} />
      <ellipse cx="124" cy="214" rx="7" ry="4.5" transform="rotate(-45 124 214)" fill={metal} {...EDGE} />
      <circle cx="172" cy="230" r="26" fill={mix('--primary', 40)} {...EDGE} />
      <path d="M196 224 Q214 222 212 238 M148 222 L136 214" {...STROKE(mix('--primary', 60), 5)} />
      <ellipse cx="172" cy="206" rx="10" ry="5" fill={mix('--primary', 40)} {...EDGE} />
      <rect x="236" y="214" width="16" height="22" rx="4" fill={WHITE} {...EDGE} />
      <rect x="233" y="208" width="22" height="8" rx="3" fill={metal} {...EDGE} />
      <circle cx="238" cy="262" r="12" fill={mix('--text-faint', 30)} {...EDGE} />
      <rect x="232" y="256" width="12" height="4" rx="1" fill={WHITE} />
    </g>
  )
}

// ── A plant, from its roots up ─────────────────────────────────────────────────

function Plant() {
  const leaf = mix('--success', 55)
  const wood = mix('--warn', 45, 'var(--text-faint)')
  return (
    <g>
      <rect x="0" y="260" width="300" height="140" fill={mix('--warn', 18, 'var(--surface)')} />
      <path d="M0 260 H300" {...STROKE('var(--border-hi)', 2)} />
      {/* Roots. */}
      <g {...STROKE(wood, 6)}>
        <path d="M150 262 Q150 300 130 330 Q120 350 100 362 M150 280 Q168 310 196 322 M150 290 Q146 334 160 372 M130 330 Q110 328 92 316" />
      </g>
      <circle cx="238" cy="300" r="6" fill={BLACK} /><circle cx="60" cy="340" r="5" fill={BLACK} />
      {/* The trunk with bark, branches, a canopy of leaves and fruit. */}
      <path d="M134 262 Q140 200 128 150 L172 150 Q160 200 166 262 Z" fill={wood} {...EDGE} />
      <path d="M146 250 Q150 200 142 160 M158 240 Q160 210 156 170" {...STROKE(BLACK, 2)} opacity=".5" />
      <path d="M130 170 Q90 150 70 112 M170 170 Q214 150 236 112" {...STROKE(wood, 12)} />
      <circle cx="150" cy="86" r="62" fill={leaf} {...EDGE} />
      <circle cx="82" cy="104" r="36" fill={leaf} {...EDGE} />
      <circle cx="222" cy="104" r="36" fill={leaf} {...EDGE} />
      <path d="M118 66 Q130 54 142 66 Q130 78 118 66 Z M172 104 Q184 92 196 104 Q184 116 172 104 Z" fill={mix('--success', 80)} {...EDGE} />
      <circle cx="104" cy="120" r="9" fill={mix('--danger', 75)} {...EDGE} />
      <circle cx="196" cy="62" r="9" fill={mix('--danger', 75)} {...EDGE} />
      {/* A flower and its bud, low on the right. */}
      <path d="M262 262 V224" {...STROKE(leaf, 4)} />
      <g fill={mix('--warn', 80)} {...EDGE}>
        {[0, 72, 144, 216, 288].map((a) => <ellipse key={a} cx="262" cy="204" rx="7" ry="12" transform={`rotate(${a} 262 216) translate(0 -10)`} />)}
      </g>
      <circle cx="262" cy="214" r="6" fill={mix('--warn', 40)} />
      <path d="M232 262 V240" {...STROKE(leaf, 3)} />
      <ellipse cx="232" cy="232" rx="5" ry="9" fill={mix('--danger', 55)} {...EDGE} />
    </g>
  )
}

const ART = { outfit: Outfit, traditional: Traditional, table: Table, plant: Plant }

// Nothing for a board it does not draw.
export default function ThingArt({ art }) {
  const Art = ART[art]
  return Art ? <Art /> : null
}
