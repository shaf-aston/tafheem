/**
 * Starred, Narrators, Scholars and Terms behind one round button beside the search's
 * mic, so on a phone the books are not pushed down by a row of chips. The
 * button wears the More mark the bottom bar uses and is tinted while one of
 * the four is open, so the reader can see where they are. Pressed, the four
 * rise in a BottomSheet (centred on a wider screen) as MenuRows, big enough for a thumb.
 */
import { useState } from 'react'

import BottomSheet from '../ui/BottomSheet'
import CloseButton from '../ui/CloseButton'
import MenuRow from '../ui/MenuRow'
import MoreIcon from '../ui/MoreIcon'

const LABEL = 'Starred, narrators, scholars and terms'

export default function HadithMoreMenu({ items, accent }) {
  const [open, setOpen] = useState(false)
  const on = items.some((item) => item.on)

  return (
    <div className="shrink-0" style={{ '--c': accent }}>
      <button
        type="button"
        aria-label={LABEL}
        title={LABEL}
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
        <BottomSheet label={LABEL} onClose={() => setOpen(false)} className="p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] flex flex-col gap-1">
          <div aria-hidden="true" className="sm:hidden self-center w-10 h-1 mb-1 rounded-full bg-[var(--border)]" />
          <div className="flex items-center justify-between gap-3 px-3 pb-2">
            <h2 className="type-label text-[var(--text-faint)]">More in Hadith</h2>
            <CloseButton onClick={() => setOpen(false)} />
          </div>
          {items.map(({ label, pick, ...row }) => (
            <MenuRow key={label} label={label} accent={accent} picked={row.on} {...row} onClick={() => { setOpen(false); pick() }} />
          ))}
        </BottomSheet>
      )}
    </div>
  )
}
