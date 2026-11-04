/**
 * One science's product-breakdown tree, drawn only.
 *
 * Every position comes from lib/shell/pbsLayout (root box, branch boxes, kid boxes,
 * every line of every label, every connector), and every chrome colour from the
 * theme; a branch's own accent (`c.bar`/`c.head`/`c.fill`) is content, carried
 * straight from lib/shell/pbsData, the same way TimelineMap takes its accent from a
 * prop rather than deciding one. This file decides no position, size or colour of its own.
 *
 * SVG text sets `lang`/`dir` directly rather than through ArabicText: a tight,
 * many-sizes diagram needs the pixel sizes tuned for it (config/pbsChart.json), not the
 * prose size ladder ArabicText hands out elsewhere in the app.
 */
import { useMemo, useRef } from 'react'

import knobs from '../../config/pbsChart.json'
import { namesOf } from '../../lib/shell/pbsFit'
import { layoutChart } from '../../lib/shell/pbsLayout'
import { useTextMeasure } from '../../lib/shell/useTextMeasure'

const M_ = knobs.margin

/** Button semantics only for a box that opens something: deeper (with a › hint) or, for a `leaf` (a branch's `leaf`, a kid's fourth item), a card without one. */
const zoomable = (hasKids, go) => hasKids
  ? {
    role: 'button',
    tabIndex: 0,
    onClick: go,
    onKeyDown: (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go() } },
  }
  : {}

/** The "›" hint that a box has deeper topics. */
const Arrow = ({ box }) => (
  <text x={box.x + knobs['hint-pad'] / 2} y={box.y + box.h / 2 + 6} textAnchor="middle" fontSize="20" fontWeight="700" fill="var(--text)" fillOpacity=".8" aria-hidden="true">›</text>
)

/** A box's words: its Arabic name, over its English if it has one, every line placed by the layout. */
const Label = ({ box, subFill }) => {
  const { label } = box
  return (
    <>
      <text textAnchor="middle" fontSize={label.size} fontWeight="700" fill="var(--text)" lang="ar" dir="rtl">
        {label.lines.map((line, i) => <tspan key={i} x={box.cx} y={line.y}>{line.text}</tspan>)}
      </text>
      {label.sub && (
        <text textAnchor="middle" fontSize={label.sub.size} fill="var(--text)" fillOpacity={subFill}>
          {label.sub.lines.map((line, i) => <tspan key={i} x={box.cx} y={line.y}>{line.text}</tspan>)}
        </text>
      )}
    </>
  )
}

/** With onZoom the chart is a group of buttons, not one picture: role=img would hide them from assistive tech. */
export default function PbsChart({ config, activeBranch, onHoverBranch, onZoom }) {
  const svg = useRef(null)
  const measure = useTextMeasure(svg, useMemo(() => namesOf(config), [config]))
  const L = useMemo(() => layoutChart(config, measure), [config, measure])

  return (
    <svg
      ref={svg}
      viewBox={`0 0 ${L.width} ${L.height}`}
      className="block w-full h-auto"
      role={onZoom ? 'group' : 'img'}
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
        <Label box={L.root} subFill={knobs.levels.root['sub-opacity']} />
      </g>

      <path d={L.trunkPath} stroke="var(--border-hi)" strokeWidth="1.6" fill="none" />
      <path d={L.busPath} stroke="var(--border-hi)" strokeWidth="1.6" fill="none" />

      {L.branches.map(({ branch: b, i, box, stemPath, spinePath, kids }) => {
        const active = activeBranch == null || activeBranch === i
        return (
          <g
            key={i}
            className="pbs-rise"
            style={{ '--d': `calc(var(--motion-stagger-ms) * ${5 + i * 3} * 1ms)`, opacity: active ? 1 : 0.18, transition: 'opacity calc(var(--motion-spring-ms) * 1ms * var(--motion-scale)) ease' }}
          >
            <path d={stemPath} stroke="var(--border-hi)" strokeWidth="1.6" fill="none" markerEnd="url(#pbs-m-root)" />
            <g
              {...zoomable(b.hasKids, () => onZoom([i]))}
              className={b.hasKids ? 'pbs-branch cursor-pointer' : undefined}
              // A mouse only: a finger's tap also fires these, and the fade then stuck until the next tap.
              onPointerEnter={(e) => e.pointerType === 'mouse' && onHoverBranch?.(i)}
              onPointerLeave={(e) => e.pointerType === 'mouse' && onHoverBranch?.(null)}
            >
              <rect x={box.x} y={box.y} width={box.w} height={box.h} rx="12" fill={b.c.head} stroke={b.c.bar} strokeWidth="1.3" />
              <Label box={box} subFill={knobs.levels.branch['sub-opacity']} />
              {box.hint && <Arrow box={box} />}
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
                  <Label box={kbox} subFill={knobs.levels.kid['sub-opacity']} />
                  {kbox.hint && <Arrow box={kbox} />}
                </g>
              </g>
            ))}
          </g>
        )
      })}

      {L.rule != null && (
        <g className="pbs-rise" style={{ '--d': `${400 + L.branches.length * 70}ms` }}>
          <line x1={M_} y1={L.rule} x2={L.width - M_} y2={L.rule} stroke="var(--border)" strokeWidth="1" />
          {config.footnote.map((line, i) => (
            <text key={i} x={M_} y={L.rule + knobs['note-drop'] + i * knobs['line-pitch']} fontSize={knobs['note-size']} fill="var(--text-faint)">
              {line}
            </text>
          ))}
        </g>
      )}
    </svg>
  )
}
