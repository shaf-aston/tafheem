/**
 * A pop-up that rises from the bottom on a phone and sits centred on a wider
 * screen. Native <dialog> through useModal, so Esc, the backdrop, the focus trap
 * and focus returning to the opener come free; the page behind stops scrolling
 * through the :modal rule in styles/components.css.
 *
 * Mounted only while open, by default. Closing by unmounting skips the browser's
 * own focus return, so the opener is noted on the first render and handed focus
 * back here. A sheet that has to keep its place while closed (Settings' scroll,
 * the sections' edit mode) is always mounted and told `open` instead: it closes
 * in place and the browser returns focus itself. That one wears .phone-sheet
 * (styles/components.css), which also seats its box on the foot of a phone with
 * room for the home bar and lets its tiles follow it up.
 *
 * `width` is a name from theme.json's sheet group: narrow, standard or wide, never
 * wider than 92% of the screen. A heading inside names it with `labelledBy`, else `label`.
 *
 * `held`: neither Esc nor the backdrop closes it, and a browser that closes it
 * anyway (Chrome lets a second Esc through) finds it open again: for a sheet
 * whose own button is the only way on (a recovery code, shown once).
 */
import { useEffect, useState } from 'react'

import { closeOnBackdrop, useModal } from '../../../lib/hooks/useModal'

// Written out, since a class built from a name is a class Tailwind never sees.
const WIDTH = {
  narrow: 'sm:max-w-[min(var(--sheet-narrow),92vw)]',
  standard: 'sm:max-w-[min(var(--sheet-standard),92vw)]',
  wide: 'sm:max-w-[min(var(--sheet-wide),92vw)]',
}

export default function BottomSheet({ label, labelledBy, onClose, open, width = 'standard', held = false, className = '', children }) {
  const kept = open !== undefined
  const dialog = useModal(kept ? open : true, held)
  const [opener] = useState(() => document.activeElement)
  useEffect(() => (kept ? undefined : () => opener?.focus?.()), [kept, opener])
  return (
    <dialog
      ref={dialog}
      aria-label={labelledBy ? undefined : label}
      aria-labelledby={labelledBy}
      onClose={held ? () => dialog.current?.showModal() : onClose}
      onClick={held ? undefined : closeOnBackdrop(onClose)}
      className={`m-0 mt-auto sm:m-auto p-0 w-full max-w-none ${WIDTH[width]} max-h-[100dvh] bg-transparent ${kept ? 'phone-sheet' : ''}`}
    >
      {/* A click inside the box is not on the backdrop, so it never reaches closeOnBackdrop's target check. */}
      <div
        className={`bg-[var(--surface)] border border-[var(--border-hi)] rounded-t-[var(--radius-md)]
          sm:rounded-[var(--radius-md)] e2 ${className}`}
      >
        {children}
      </div>
    </dialog>
  )
}
