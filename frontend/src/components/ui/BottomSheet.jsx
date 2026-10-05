/**
 * A pop-up that rises from the bottom on a phone and sits centred on a wider
 * screen. Mounted only while open. Native <dialog> through useModal, so Esc,
 * the backdrop, the focus trap and focus returning to the opener come free;
 * the page behind stops scrolling through the :modal rule in styles/components.css.
 * Closing by unmounting skips the browser's own focus return, so the opener
 * is noted on the first render and handed focus back here.
 */
import { useEffect, useState } from 'react'

import { useModal } from '../../lib/useModal'

export default function BottomSheet({ label, onClose, className = '', children }) {
  const dialog = useModal(true)
  const [opener] = useState(() => document.activeElement)
  useEffect(() => () => opener?.focus?.(), [opener])
  return (
    <dialog
      ref={dialog}
      aria-label={label}
      onClose={onClose}
      onClick={(e) => e.target === dialog.current && onClose()}
      className="m-0 mt-auto sm:m-auto p-0 w-full max-w-none sm:max-w-[var(--sheet-standard)] max-h-[100dvh] bg-transparent"
    >
      <div
        className={`bg-[var(--surface)] border border-[var(--border-hi)] rounded-t-[var(--radius-md)]
          sm:rounded-[var(--radius-md)] shadow-[var(--shadow-pop)] ${className}`}
      >
        {children}
      </div>
    </dialog>
  )
}
