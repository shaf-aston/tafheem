/**
 * The one way in for a guest, wherever it is offered: the header, Home's
 * progress line, Grow. A person mark and the app's own colour, so it reads as
 * the same door each time; it opens the profile dialog itself.
 */
import { useState } from 'react'

import SmallButton from '../ui/SmallButton'
import ProfileDialog from './ProfileDialog'

export default function LogInButton({ children = 'Log in', title = 'Log in to keep your progress on any device', className = '' }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <SmallButton
        onClick={() => setOpen(true)}
        title={title}
        aria-haspopup="dialog"
        className={`inline-flex items-center gap-1.5 shrink-0 font-semibold text-[var(--primary-hi)]
          border-[color-mix(in_srgb,var(--primary)_45%,var(--border))] bg-[color-mix(in_srgb,var(--primary)_8%,transparent)] ${className}`}
      >
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
          <circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" />
        </svg>
        {children}
      </SmallButton>
      {open && <ProfileDialog onClose={() => setOpen(false)} />}
    </>
  )
}
