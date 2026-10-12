/**
 * One science's product-breakdown tree, drawn only.
 *
 * Every position comes from lib/pbsLayout (root box, branch boxes, kid boxes,
 * every connector), and every chrome colour from the theme; a branch's own
 * accent (`c.bar`/`c.fill`/`c.text`) is content, carried straight from
 * lib/pbsData, the same way TimelineMap takes its accent from a prop rather
 * than deciding one. This file decides no position and no colour of its own.
 *
 * SVG text sets `lang`/`dir` directly rather than through ArabicText: a tight,
 * many-sizes diagram needs the pixel sizes tuned for it, not the prose size
 * ladder ArabicText hands out elsewhere in the app.
 */
import { layoutChart } from '../../lib/pbsLayout'

const M_ = 18

/** Button semantics only for a box that opens something deeper. */
const zoomable = (hasKids, go) => hasKids
  ? {
    role: 'button',
    tabIndex: 0,
    onClick: go,
    onKeyDown: (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go() } },
  }
  : {}

/** The "›" hint that a box has deeper topics. */
const Arrow = ({ x, y, fill }) => (
  <text x={x} y={y} fontSize="20" fontWeight="700" fill={fill} fillOpacity=".8" aria-hidden="true">›</text>
)

export default function PbsChart({ config, activeBranch, onHoverBranch, onZoom }) {
  const L = layoutChart(config)

  return (
    <svg
      viewBox={`0 0 ${L.width} ${L.height}`}
      className="block w-full h-auto"
      role="img"
      aria-label={config.root.en || config.root.ar}
    >
      <defs>
        <marker id="pbs-m-root" markerWidth="7" markerHeight="7" refX="6.2" refY="3" orient="auto">
          <path d="M0,0 L6.5,3 L0,6 Z" fill="var(--border-hi)" />
        </marker>
        {L.branches.map(({ branch, i }) => (
          <marker key={i} id={`pbs-m${i}`} markerWidth="7" markerHeight="7" refX="6.2" refY="3" orient="auto">
            <path d="M0,0 L6.5,3 L0,6 Z" fill={branch.c.bar} />
          </marker>
        ))}
      </defs>

      <g className="pbs-rise">
        <rect x={L.root.x} y={L.root.y} width={L.root.w} height={L.root.h} rx="14" fill="var(--surface-hi)" />
        <text x={L.root.cx} y={L.root.textY} textAnchor="middle" fontSize="28" fontWeight="700" fill="var(--text)" lang="ar" dir="rtl">
          {config.root.ar}
        </text>
        <text x={L.root.cx} y={L.root.subTextY} textAnchor="middle" fontSize="12" fill="var(--text)" fillOpacity=".85">
          {config.root.en && `(${config.root.en})`}
        </text>
      </g>

      <path d={L.trunkPath} stroke="var(--border-hi)" strokeWidth="1.6" fill="none" />
      <path d={L.busPath} stroke="var(--border-hi)" strokeWidth="1.6" fill="none" />

      {L.branches.map(({ branch: b, i, box, stemPath, spinePath, kids }) => {
        const active = activeBranch == null || activeBranch === i
        return (
          <g
            key={i}
            className="pbs-rise"
            style={{ '--d': `${120 + i * 70}ms`, opacity: active ? 1 : 0.18, transition: 'opacity .25s ease' }}
          >
            <path d={stemPath} stroke="var(--border-hi)" strokeWidth="1.6" fill="none" markerEnd="url(#pbs-m-root)" />
            <g
              {...zoomable(b.hasKids, () => onZoom([i]))}
              className={b.hasKids ? 'pbs-branch cursor-pointer' : undefined}
              onMouseEnter={() => onHoverBranch?.(i)}
              onMouseLeave={() => onHoverBranch?.(null)}
            >
              <rect x={box.x} y={box.y} width={box.w} height={box.h} rx="12" fill={b.c.bar} />
              <text x={box.cx} y={box.textY} textAnchor="middle" fontSize="17" fontWeight="700" fill="var(--text)" lang="ar" dir="rtl">
                {b.ar}
              </text>
              <text x={box.cx} y={box.subTextY} textAnchor="middle" fontSize="10" fill="var(--text)" fillOpacity=".9">
                {b.en && `(${b.en})`}
              </text>
              {b.hasKids && <Arrow x={box.x + 14} y={box.y + box.h / 2 + 6} fill="var(--text)" />}
            </g>
            {kids.length > 0 && <path d={spinePath} stroke={b.c.bar} strokeWidth="1.5" fill="none" />}
            {kids.map(({ kid: k, j, box: kbox, connectorPath }) => (
              <g key={j} className="pbs-rise" style={{ '--d': `${220 + i * 70 + j * 26}ms` }}>
                <path d={connectorPath} stroke={b.c.bar} strokeWidth="1.5" fill="none" markerEnd={`url(#pbs-m${i})`} />
                <g
                  {...zoomable(k[2], () => onZoom([i, j]))}
                  className={k[2] ? 'pbs-kid cursor-pointer' : undefined}
                >
                  <rect x={kbox.x} y={kbox.y} width={kbox.w} height={kbox.h} rx="10"
                    fill={b.c.fill} stroke={b.c.bar} strokeWidth="1.3" />
                  <text x={kbox.cx} y={kbox.textY} textAnchor="middle" fontSize="15.5" fontWeight="700" fill={b.c.text} lang="ar" dir="rtl">
                    {k[0]}
                  </text>
                  <text x={kbox.cx} y={kbox.subTextY} textAnchor="middle" fontSize="9.5" fill={b.c.text} fillOpacity=".7">
                    {k[1] && `(${k[1]})`}
                  </text>
                  {k[2] && <Arrow x={kbox.x + 12} y={kbox.y + kbox.h / 2 + 5} fill={b.c.text} />}
                </g>
              </g>
            ))}
          </g>
        )
      })}

      <g className="pbs-rise" style={{ '--d': `${400 + L.branches.length * 70}ms` }}>
        <line x1={M_} y1={L.rule} x2={L.width - M_} y2={L.rule} stroke="var(--border)" strokeWidth="1" />
        {config.footnote.map((line, i) => (
          <text key={i} x={M_} y={L.rule + 25 + i * 18} fontSize="11.5" fill="var(--text-faint)">
            {line}
          </text>
        ))}
      </g>
    </svg>
  )
}
