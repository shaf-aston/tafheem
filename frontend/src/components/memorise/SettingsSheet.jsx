/**
 * What is chosen once and left (how you answer, book, how much is hidden, the
 * translation), behind one quiet Settings pill that also says what is chosen.
 * Pressed, it rises as a BottomSheet, one captioned row each, big enough for a
 * thumb: a small floating card ran off the screen's edge and its captions lost
 * their rows.
 */
import { useState } from 'react'

import BottomSheet from '../ui/overlays/BottomSheet'

export default function SettingsSheet({ summary, rows, accent }) {
  const [open, setOpen] = useState(false)

  return (
    <>
      <button
        type="button"
        aria-haspopup="dialog"
        onClick={() => setOpen(true)}
        style={{ '--c': accent }}
        className="mem-settings press tap type-ui"
      >
        Settings
        {/* What is chosen, faint, so the pill reads as one word first. */}
        {summary && <span className="mem-settings-summary">{summary}</span>}
        <svg aria-hidden="true" viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 9l6 6 6-6" /></svg>
      </button>
      {open && (
        <BottomSheet label="Memorise settings" onClose={() => setOpen(false)} className="p-4 pb-[max(1rem,env(safe-area-inset-bottom))] flex flex-col gap-4">
          <div aria-hidden="true" className="sm:hidden self-center w-10 h-1 rounded-full bg-[var(--border)]" />
          {rows.map(({ caption, control }) => (
            <div key={caption} className="flex flex-col gap-1.5">
              <span className="eyebrow">{caption}</span>
              {control}
            </div>
          ))}
          <button type="button" onClick={() => setOpen(false)} className="press tap self-end px-4 py-2 rounded-full type-ui font-medium" style={{ color: accent }}>
            Done
          </button>
        </BottomSheet>
      )}
    </>
  )
}
