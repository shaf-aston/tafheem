/**
 * The phone bar's places, drawn while it is being edited: one slot per place on
 * the bar, each holding its tab or waiting for one. A tab in a slot is dragged
 * by the whole slot; letting a tab go over a slot puts it there (lib/dock.js).
 * Draws what it is given and decides nothing.
 */
import TabMark from '../ui/TabMark'

export default function DockSlots({ size, tabs, colorOf, drag, grip }) {
  return (
    <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${size}, minmax(0, 1fr))` }}>
      {Array.from({ length: size }, (_, i) => {
        const tab = tabs[i]
        const over = drag?.over === String(i)
        return (
          <div
            key={i}
            data-slot={i}
            {...(tab ? grip(tab.id) : {})}
            style={{ ...(tab ? { '--c': colorOf(tab.id), touchAction: 'none' } : null) }}
            className={`grid place-items-center gap-0.5 min-h-14 rounded-[var(--radius-sm)] border type-tiny font-semibold select-none
              ${tab ? 'bg-[var(--bg)] text-[var(--c)] cursor-grab' : 'border-dashed text-[var(--text-faint)]'}
              ${over ? 'border-[var(--c,var(--text))] bg-[var(--surface-hi)]' : tab ? 'border-[var(--border-hi)]' : 'border-[var(--border)]'}
              ${drag?.id === tab?.id ? 'opacity-40' : ''}`}
          >
            {tab ? (
              <>
                <span aria-hidden="true"><TabMark tab={tab} /></span>
                {tab.short}
              </>
            ) : <span aria-hidden="true">+</span>}
          </div>
        )
      })}
    </div>
  )
}
