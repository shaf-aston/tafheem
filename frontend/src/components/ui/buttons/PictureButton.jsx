/**
 * Choose a picture: a photo of a page, a screenshot, a scan.
 *
 * Drawn as the microphone's twin (MicButton), the round button beside a search
 * box, because the two are the same kind of thing: another way to put words in
 * the box than typing them. On a phone the system sheet offers the camera and
 * the photo library both; `capture` would have taken the library away.
 */
import { useRef } from 'react'

import FilePick from '../inputs/FilePick'

export default function PictureButton({ onPicked, title = 'Read a picture of a page', disabled = false }) {
  const pick = useRef(null)
  return (
    <>
      <button
        type="button"
        onClick={() => pick.current?.()}
        disabled={disabled}
        aria-label={title}
        title={title}
        className="relative w-10 h-10 shrink-0 grid place-items-center rounded-full border border-[var(--border-hi)]
          text-[var(--text-faint)] hover:text-[var(--text)] hover:border-[var(--text-faint)] transition-colors disabled:opacity-40"
      >
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.7"
          strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M4 8.5A1.5 1.5 0 0 1 5.5 7h2l1.4-2h6.2l1.4 2h2A1.5 1.5 0 0 1 20 8.5v9a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 17.5z" />
          <circle cx="12" cy="13" r="3.5" />
        </svg>
      </button>
      <FilePick pick={pick} accept="image/*" onPicked={onPicked} />
    </>
  )
}
