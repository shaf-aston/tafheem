/**
 * The other narrations of a hadith number (Muslim 1620a, b, c...) in one closed fold:
 * a row per narration (its own narrators, where it meets this chain, what it borrows
 * from it, then its own wording) or, under "Tree", one drawing of every chain together, or,
 * under "Words", each telling's text with the words only it has marked. Above them, how many
 * narrators carry the number at each place of the chains (FamilyRoutes).
 * Tapping a row or a leaf opens that hadith.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { narrationFamilyQuery } from '../../api'
import { familyTree } from '../../lib/familyTree'

import ArabicText from './ArabicText'
import Disclosure from './Disclosure'
import FamilyRoutes from './FamilyRoutes'
import FamilyWords from './FamilyWords'
import Segmented from './Segmented'

const VIEWS = [{ id: 'rows', label: 'Rows' }, { id: 'tree', label: 'Tree' }]
const WORDS_VIEW = { id: 'words', label: 'Words' }

// Tree grid, in px: one column and one row of the layout, and a narrator's box in it.
const CELL = { w: 112, h: 52, pill: { w: 100, h: 26 } }

const TONES = {
  own: 'border-[var(--border)] text-[var(--text)]',
  meet: 'border-[var(--warn)] text-[var(--text)]',
  borrowed: 'border-dashed border-[var(--border)] text-[var(--text-faint)] opacity-70',
}

function Row({ part, accent, onOpen, onNarrator }) {
  const pills = [
    ...part.own.map((n) => ({ ...n, tone: 'own' })),
    ...(part.meet ? [{ ...part.meet, tone: 'meet' }] : []),
    ...part.borrowed.map((n) => ({ ...n, tone: 'borrowed' })),
  ]
  return (
    <li className="py-2 border-t border-[var(--border)] first:border-t-0">
      <div className="flex items-start gap-2">
        <button
          type="button"
          onClick={() => onOpen(part)}
          aria-label={`Open ${part.part}`}
          style={{ color: accent, borderColor: accent }}
          className="press type-tiny shrink-0 w-7 h-7 grid place-items-center rounded-full border"
        >
          {part.part}
        </button>
        <div dir="rtl" className="flex flex-wrap items-center gap-1 min-w-0">
          {pills.map((n, i) => (
            <span key={`${n.id}-${i}`} className="flex items-center gap-1">
              {i > 0 && <span aria-hidden="true" className="text-[var(--text-faint)] type-tiny">&larr;</span>}
              <button type="button" onClick={() => onNarrator?.(n.id)} className={`press rounded-full border px-2 py-0.5 ${TONES[n.tone]}`}>
                <ArabicText size="tiny">{n.name}</ArabicText>
              </button>
            </span>
          ))}
        </div>
      </div>
      {part.said && (
        <button type="button" onClick={() => onOpen(part)} className="press block w-full text-start mt-1.5 ps-9">
          <ArabicText as="p" size="sm" className="block m-0 text-[var(--text-dim)] line-clamp-2">{part.said}</ArabicText>
        </button>
      )}
    </li>
  )
}

function Tree({ parts, accent, onOpen }) {
  // Each branch runs its whole chain: its own narrators, where it meets this one, then what it borrows.
  const tree = familyTree(parts.map((p) => ({ part: p.part, narrators: [...p.own, ...(p.meet ? [p.meet] : []), ...p.borrowed] })))
  const at = (x, y) => [x * CELL.w + CELL.w / 2, y * CELL.h + CELL.h / 2]
  const byId = new Map(tree.nodes.map((n) => [n.key, n]))
  const line = (from, to) => {
    const [x1, y1] = at(from.x, from.y ?? from.depth)
    const [x2, y2] = at(to.x, to.y ?? to.depth)
    return <line key={`${x1},${y1}>${x2},${y2}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--border)" strokeWidth="1.5" />
  }
  return (
    // Its own box scrolls, so a wide family never pushes the page sideways.
    <div data-tree className="overflow-x-auto">
      <svg width={tree.columns * CELL.w} height={(tree.rows + 1) * CELL.h} role="img" aria-label="Chains of every narration">
        {tree.edges.map(([a, b]) => line(byId.get(a), byId.get(b)))}
        {tree.leaves.map((l) => line(byId.get(l.parent), l))}
        {tree.nodes.map((n) => {
          const [cx, cy] = at(n.x, n.depth)
          return (
            <foreignObject key={n.key} x={cx - CELL.pill.w / 2} y={cy - CELL.pill.h / 2} width={CELL.pill.w} height={CELL.pill.h}>
              <div title={n.name} className="h-full grid place-items-center rounded-full border border-[var(--border)] bg-[var(--surface)] px-2 overflow-hidden">
                <ArabicText size="tiny" className="block max-w-full truncate whitespace-nowrap">{n.name}</ArabicText>
              </div>
            </foreignObject>
          )
        })}
        {tree.leaves.map((l) => {
          const [cx, cy] = at(l.x, l.y)
          const part = parts.find((p) => p.part === l.part)
          return (
            <g
              key={l.part} role="button" tabIndex={0} aria-label={`Open ${l.part}`} className="cursor-pointer"
              onClick={() => onOpen(part)} onKeyDown={(e) => e.key === 'Enter' && onOpen(part)}
            >
              <circle cx={cx} cy={cy} r="13" fill="var(--surface)" stroke={accent} />
              <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central" fill={accent} className="type-tiny">{l.part}</text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}

export default function NarrationFamily({ collection, number, part, count, accent, onOpen, onNarrator }) {
  // Fetched on first open: most cards are never unfolded.
  const [asked, setAsked] = useState(false)
  const [view, setView] = useState('rows')
  const { data } = useQuery({ ...narrationFamilyQuery(collection, number, part), enabled: asked })
  const others = data?.parts.filter((p) => p.part !== data.viewed) ?? []
  const views = data?.parts.some((p) => p.marks.length) ? [...VIEWS, WORDS_VIEW] : VIEWS

  return (
    <Disclosure label={`${count} narrations`} onToggle={(open) => open && setAsked(true)} className="mt-3 pt-3 border-t border-[var(--border)]">
      {data && (
        <div className="space-y-2">
          <FamilyRoutes routes={data.routes} tellings={data.parts.length} accent={accent} />
          <Segmented label="View" options={views} value={view} onChange={setView} accent={accent} />
          {view === 'rows' && <ul className="list-none m-0 p-0">{others.map((p) => <Row key={p.part} part={p} accent={accent} onOpen={onOpen} onNarrator={onNarrator} />)}</ul>}
          {view === 'tree' && <Tree parts={data.parts} accent={accent} onOpen={onOpen} />}
          {view === 'words' && <FamilyWords parts={data.parts} accent={accent} onOpen={onOpen} />}
        </div>
      )}
    </Disclosure>
  )
}
