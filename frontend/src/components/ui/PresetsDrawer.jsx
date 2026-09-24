/**
 * Curated verbs grouped by form (باب). Each card carries enough data to show a
 * result the instant it is clicked, so browsing costs nothing.
 */
import { useState } from 'react'

import { SARF_PRESETS } from '../../data/sarfPresets'

import ArabicText from './ArabicText'

const TOTAL = SARF_PRESETS.reduce((n, g) => n + g.words.length, 0)

export default function PresetsDrawer({ onPick, accent }) {
  const [open, setOpen] = useState(true)

  return (
    <div style={{ '--c': accent }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="w-full flex items-center justify-between px-4 py-2.5 rounded-[var(--radius-md)]
          bg-[var(--surface)] border border-[var(--border)] hover:border-[var(--border-hi)]
          transition-colors group"
      >
        <span className="flex items-center gap-2 text-sm text-[var(--text-dim)] group-hover:text-[var(--text)] transition-colors">
          <span aria-hidden="true" className={`transition-transform ${open ? 'rotate-90' : ''}`}>▸</span>
          <span className="font-medium">Common verbs</span>
          <span className="text-[var(--text-faint)] text-xs hidden sm:inline">grouped by form (باب)</span>
        </span>
        <span className="text-[var(--text-faint)] text-xs">{TOTAL}</span>
      </button>

      {open && (
        <div className="mt-2 p-4 rounded-[var(--radius-md)] bg-[var(--surface)] border border-[var(--border)] space-y-5">
          {SARF_PRESETS.map((group) => (
            <PresetGroup key={group.id} group={group} onPick={onPick} accent={accent} />
          ))}
          <p className="text-[var(--text-faint)] text-xs text-center">
            One click fills the box and analyses it
          </p>
        </div>
      )}
    </div>
  )
}

function PresetGroup({ group, onPick, accent }) {
  return (
    <div>
      <div className="flex items-baseline gap-2 mb-2">
        <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: accent }}>
          {group.category}
        </span>
        <span className="text-[var(--text-faint)] text-xs">{group.labelEn}</span>
      </div>

      {/* A grid, not a right-to-left wrapping row. The row used to be dir="rtl",
          which packed three or four cards hard against the right edge and left
          the other half of the line empty, the emptiest thing on the page. Each
          card carries its own lang="ar", so the container never needed it. */}
      <div className="grid gap-2 grid-cols-[repeat(auto-fill,minmax(6.5rem,1fr))]">
        {group.words.map((w, i) => (
          <button
            key={w.arabic}
            type="button"
            onClick={() => onPick(w)}
            style={{ '--i': i }}
            className="rise-in flex flex-col items-center justify-center px-3 py-2
              rounded-[var(--radius-sm)] bg-[var(--surface-hi)] border border-[var(--border)]
              hover:border-[var(--c)] transition-colors"
          >
            {/* Same size as the gardaan's cells, a verb should not change size
                between the card you click and the table it opens. */}
            <ArabicText className="leading-tight text-[var(--text)]">{w.arabic}</ArabicText>
            <span className="text-[var(--text-faint)] type-tiny mt-1 text-center leading-tight" dir="ltr">
              {w.meaning}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
