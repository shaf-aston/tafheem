/**
 * The side panel for whatever was clicked in a PbsChart: a branch (its topics)
 * or a leaf topic (the أبواب inside it, from lib/pbsData's SUB lookup, plus
 * its sibling topics). Slides in over the chart, inside MapPanel's own
 * dialog — not a second nested <dialog>, which would layer wrong.
 */
import ArabicText from './ArabicText'
import { SUB } from '../../lib/pbsData'
import { readableAccent } from '../../lib/pbsAccent'

export default function PbsDetail({ chart, branchIndex, kidIndex, onSelectKid, onClose }) {
  const branch = chart.config.branches[branchIndex]
  if (!branch) return null
  const kid = kidIndex != null ? branch.kids[kidIndex] : null
  const accent = branch.c.bar
  // The border bar can stay at the branch's own colour; the headline is text
  // on the panel's dark surface, so it gets the readability floor.
  const fg = readableAccent(accent)

  const subTopics = kid
    ? (SUB[`${chart.id}.${branchIndex}.${kidIndex}`] ?? '').split('·').map((t) => t.trim()).filter(Boolean)
    : []

  return (
    <aside
      className="absolute inset-y-0 right-0 w-full max-w-[22rem] bg-[var(--surface)]
        border-l-[5px] overflow-y-auto p-5"
      style={{ borderLeftColor: accent }}
      aria-label={kid ? kid[0] : branch.ar}
    >
      <button
        type="button"
        onClick={onClose}
        title="Close"
        aria-label="Close"
        className="absolute top-3.5 right-3.5 icon-button"
      >
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M18 6 6 18M6 6l12 12" />
        </svg>
      </button>

      <p className="type-tiny tracking-widest font-bold text-[var(--text-faint)] uppercase pr-8">
        {chart.id} · {kid ? `NODE ${branchIndex + 1}.${kidIndex + 1}` : `BRANCH ${branchIndex + 1} of ${chart.config.branches.length}`}
      </p>
      <ArabicText as="p" size="lg" className="mt-2 leading-snug" style={{ color: fg }}>
        {kid ? kid[0] : branch.ar}
      </ArabicText>
      <p className="type-small text-[var(--text-dim)]">{kid ? kid[1] : branch.en}</p>

      <div className="mt-4 pt-3.5 border-t border-[var(--border)] type-small text-[var(--text-dim)] leading-relaxed">
        {kid ? (
          <>Part of <b className="text-[var(--text)]">{branch.ar}</b> ({branch.en})<br />
            within <b className="text-[var(--text)]">{chart.config.root.ar}</b><br />{chart.frame}</>
        ) : (
          <>A book-level division of <b className="text-[var(--text)]">{chart.config.root.ar}</b><br />
            {chart.en} · {chart.frame}<br />{branch.kids.length} nodes sit under it.</>
        )}
      </div>

      {kid && subTopics.length > 0 && (
        <div className="mt-4 pt-3.5 border-t border-[var(--border)]">
          <h4 className="type-tiny tracking-widest font-bold text-[var(--text-faint)] uppercase mb-2">
            Inside this node · أبوابه
          </h4>
          <ul className="m-0 p-0 list-none">
            {subTopics.map((t, i) => (
              <li key={i} className="type-body py-1.5 border-b border-dashed border-[var(--border)] last:border-b-0 text-right" dir="rtl" lang="ar">
                {t} <span className="text-[var(--text-faint)] type-small">—</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 pt-3.5 border-t border-[var(--border)]">
        <h4 className="type-tiny tracking-widest font-bold text-[var(--text-faint)] uppercase mb-2">
          {kid ? 'Alongside it · أخواته' : 'Nodes under it · أبناؤه'}
        </h4>
        <div className="flex flex-wrap gap-1.5">
          {branch.kids.map((k, j) => (
            <button
              key={j}
              type="button"
              onClick={() => onSelectKid(branchIndex, j)}
              className="type-small px-2.5 py-1 rounded-full border"
              style={j === kidIndex
                ? { background: accent, color: '#fff', borderColor: accent }
                : { borderColor: `${accent}55`, color: 'var(--text)' }}
            >
              <ArabicText as="span">{k[0]}</ArabicText>
            </button>
          ))}
        </div>
      </div>
    </aside>
  )
}
