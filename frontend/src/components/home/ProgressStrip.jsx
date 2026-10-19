/** XP and streak when logged in, or the way to log in. One job: the progress line of Home. */
import { useState } from 'react'

import XpCard from '../profile/XpCard'
import ProfileDialog from '../profile/ProfileDialog'

export default function ProgressStrip({ name, rewards, streak, copy }) {
  const [asking, setAsking] = useState(false)
  if (!name) {
    return (
      <>
        <p className="flex flex-wrap items-center gap-x-2 text-[var(--text-dim)]">
          <span>{copy.guest}</span>
          <button type="button" onClick={() => setAsking(true)} aria-haspopup="dialog"
            className="press min-h-11 px-1 font-semibold text-[var(--primary-hi)] underline underline-offset-4">
            {copy['guest-go']}
          </button>
        </p>
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
