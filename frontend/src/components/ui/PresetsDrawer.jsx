/**
 * Curated verbs grouped by form (باب). Each card carries enough data to show a
 * result the instant it is clicked, so browsing costs nothing.
 */
import { SARF_PRESETS } from '../../data/sarfPresets'

import ArabicText from './ArabicText'
import Disclosure from './Disclosure'

const TOTAL = SARF_PRESETS.reduce((n, g) => n + g.words.length, 0)

export default function PresetsDrawer({ onPick, accent }) {
  return (
    <Disclosure
      framed
      tone="strong"
      defaultOpen
      label={(
        <span className="flex items-baseline justify-between gap-2">
          <span className="flex items-baseline gap-2">
            Common verbs
            <span className="type-small font-normal text-[var(--text-faint)] hidden sm:inline">grouped by form (باب)</span>
          </span>
          <span className="type-small font-normal text-[var(--text-faint)]">{TOTAL}</span>
        </span>
      )}
    >
      <div style={{ '--c': accent }} className="p-[var(--space-card)] border-t border-[var(--border)] bg-[var(--surface)] space-y-5">
        {SARF_PRESETS.map((group) => (
          <PresetGroup key={group.id} group={group} onPick={onPick} />
        ))}
        <p className="type-small text-[var(--text-faint)] text-center">
          One click fills the box and analyses it
        </p>
      </div>
    </Disclosure>
  )
}

function PresetGroup({ group, onPick }) {
  return (
    <div>
      <div className="flex items-baseline gap-2 mb-2">
        <span className="eyebrow font-semibold text-[var(--c)]">{group.category}</span>
        <span className="type-small text-[var(--text-faint)]">{group.labelEn}</span>
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
            className="card-tile rise-in lift press flex flex-col items-center justify-center
              hover:border-[var(--c)] focus-visible:border-[var(--c)]"
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
