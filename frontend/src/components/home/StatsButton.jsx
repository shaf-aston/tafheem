/**
 * Home's progress on a phone, where the column (StatsRail) has no room: one small
 * button that opens the same profile popup as the header's level, so both lead
 * to one place. Its drawing and words are home.json `stats`.
 */
import { useState } from 'react'

import knobs from '../../home.json'
import ProfileDialog from '../profile/ProfileDialog'

const { stats: copy } = knobs

export default function StatsButton() {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button type="button" onClick={() => setOpen(true)} title={copy.button} aria-label={copy.button}
        aria-haspopup="dialog" className="icon-button shrink-0">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2"
          strokeLinecap="round" aria-hidden="true">
          {copy.icon.map((d) => <path key={d} d={d} />)}
        </svg>
      </button>
      {open && <ProfileDialog onClose={() => setOpen(false)} />}
    </>
  )
}
