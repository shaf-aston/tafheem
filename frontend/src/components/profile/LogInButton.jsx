/**
 * The one way in for a guest, wherever it is offered: Home's progress line and
 * Grow wear the call to action (.cta), the header the same pill unfilled
 * (`quiet`), so it never shouts over the tabs. It opens the profile dialog itself.
 */
import { useState } from 'react'

import ProfileDialog from './ProfileDialog'

export default function LogInButton({ children = 'Log in', title = 'Log in to keep your progress on any device', quiet = false }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        title={title}
        aria-haspopup="dialog"
        className={`cta type-small ${quiet ? 'cta-quiet' : ''}`}
      >
        {children}
        <span aria-hidden="true" className="cta-arrow">→</span>
      </button>
      {open && <ProfileDialog onClose={() => setOpen(false)} />}
    </>
  )
}
