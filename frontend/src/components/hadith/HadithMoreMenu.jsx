/**
 * Starred, Narrators and Scholars behind one round button beside the search's
 * mic, so on a phone the books are not pushed down by a row of chips. The
 * button wears the More mark the bottom bar uses and is tinted while one of
 * the three is open, so the reader can see where they are. Pressed, the three
 * rise in a BottomSheet (centred on a wider screen), big enough for a thumb.
 */
import { useState } from 'react'

import BottomSheet from '../ui/BottomSheet'
import MoreIcon from '../ui/MoreIcon'

export default function HadithMoreMenu({ items, accent }) {
  const [open, setOpen] = useState(false)
  const on = items.some((item) => item.on)

  return (
    <div className="shrink-0" style={{ '--c': accent }}>
      <button
        type="button"
        aria-label="Starred, narrators and scholars"
        title="Starred, narrators and scholars"
        aria-haspopup="dialog"
        onClick={() => setOpen(true)}
        className={`press w-10 h-10 grid place-items-center rounded-full border transition-colors ${
          on
            ? 'border-[var(--c)] text-[var(--c)]'
            : 'border-[var(--border)] text-[var(--text-faint)] hover:text-[var(--text)] hover:border-[var(--text-faint)]'
        }`}
      >
        <MoreIcon size={20} />
      </button>
      {open && (
        <BottomSheet label="Starred, narrators and scholars" onClose={() => setOpen(false)} className="p-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] flex flex-col" >
          <div aria-hidden="true" className="sm:hidden self-center w-10 h-1 my-2 rounded-full bg-[var(--border)]" />
          {items.map(({ label, hint, count, on: picked, pick }) => (
            <button
              key={label}
              type="button"
              aria-pressed={picked}
              onClick={() => { setOpen(false); pick() }}
              style={{ '--c': accent }}
              className={`press tap min-h-14 px-4 flex items-center gap-3 rounded-[var(--radius-sm)] type-body text-start transition-colors ${
                picked ? 'text-[var(--c)] bg-[var(--surface-hi)]' : 'text-[var(--text)] hover:bg-[var(--surface-hi)]'
              }`}
            >
              <span className="flex-1">{label}</span>
              <span className="type-small text-[var(--text-faint)] tabular-nums">{count > 0 ? `${count} saved` : hint}</span>
            </button>
          ))}
        </BottomSheet>
      )}
    </div>
  )
}
