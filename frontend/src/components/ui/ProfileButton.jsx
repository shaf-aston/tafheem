/** The header's "whose record is this": the name, or an invitation to type one. */
import { useState } from 'react'

import { getProfile } from '../../lib/profile'

import ProfileDialog from './ProfileDialog'

export default function ProfileButton() {
  const [name, setName] = useState(getProfile)
  const [open, setOpen] = useState(false)
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        title={name ? 'Switch name' : 'Type a name to keep your own progress'}
        aria-haspopup="dialog"
        dir="auto"
        className="type-small px-2 py-1 rounded-[var(--radius-sm)] border border-[var(--border)]
          text-[var(--text-dim)] hover:text-[var(--text)] max-w-[8rem] truncate shrink-0"
      >
        {name || "Who's learning?"}
      </button>
      {/* Mounted only while open, so each opening starts from the saved name. */}
      {open && <ProfileDialog open onClose={() => setOpen(false)} onSaved={setName} />}
    </>
  )
}
