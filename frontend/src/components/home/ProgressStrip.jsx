/** XP and streak when logged in, or the way to log in. One job: the progress line of Home. */
import { useState } from 'react'

import XpCard from '../profile/XpCard'
import ProfileDialog from '../profile/ProfileDialog'

export default function ProgressStrip({ name, rewards, streak, copy }) {
  const [asking, setAsking] = useState(false)
  if (!name) {
    return (
      <>
        <button type="button" onClick={() => setAsking(true)} aria-haspopup="dialog"
          className="press min-h-11 type-small px-3 rounded-[var(--radius-sm)] border border-[var(--border)] text-[var(--text-dim)] hover:text-[var(--text)]">
          {copy.guest}
        </button>
        {asking && <ProfileDialog onClose={() => setAsking(false)} />}
      </>
    )
  }
  return (
    <div className="space-y-2">
      <XpCard rewards={rewards} />
      {streak > 0 && (
        <p className="type-small text-[var(--text-dim)]">
          {streak === 1 ? copy['streak-one'] : `${streak} ${copy['streak-many']}`}
        </p>
      )}
    </div>
  )
}
