/**
 * A small sliders icon for how a page is read; pressed, its on/off chips (and
 * `children`) slide out beside it in the bar. Shared by the hadith books and
 * the Quran reader, so the two set their options the same way. Worn inside a
 * wrapping flex row, whose last line the chips take on a phone.
 *
 * An option marked `wide` is left off a phone, `touch` is offered only on a
 * touch screen: the choice is not hidden, it means nothing there.
 */
import { useState } from 'react'

import Chip from './Chip'
import ChipRow from './ChipRow'

const ONLY = { wide: 'hidden md:contents', touch: 'hidden pointer-coarse:contents' }

export default function ReadingOptions({ options, accent, children }) {
  const [open, setOpen] = useState(false)

  return (
    // On a phone the chips drop to a full row of their own under the bar, so
    // opening them never pushes the bar's last buttons onto a line alone.
    <div className="contents sm:flex sm:items-center sm:gap-3" style={{ '--c': accent }}>
      {open && (
        <ChipRow className="fade-in order-last basis-full sm:order-none sm:basis-auto">
          {options.map(({ label, on, set, only }) => (
            <span key={label} className={ONLY[only] ?? 'contents'}>
              <Chip tinted selected={on} accent={accent} onClick={() => set(!on)}>{label}</Chip>
            </span>
          ))}
          {children}
        </ChipRow>
      )}
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-label="Reading options"
        title="Reading options"
        className={`press tap grid place-items-center w-[var(--layout-chip)] h-[var(--layout-chip)] rounded-full transition-colors ${
          open ? 'text-[var(--c)]' : 'text-[var(--text-faint)] hover:text-[var(--text-dim)]'
        }`}
      >
        <svg aria-hidden="true" viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M4 7h10M18 7h2M4 17h4M12 17h8" />
          <circle cx="16" cy="7" r="2" />
          <circle cx="10" cy="17" r="2" />
        </svg>
      </button>
    </div>
  )
}
