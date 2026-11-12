/**
 * The header's "who is logged in": the username, or the guest's LogInButton, with the level
 * worn quietly beside it (LevelRing).
 *
 * On each load it checks the name with the server (`checkAccount`). A name the server will not
 * take from this browser (deleted in another tab, or an account this browser holds no token for)
 * logs out by itself, saying why in the log-in box, rather than every answer silently failing to
 * save. A name from before recovery codes is claimed by this browser there and then, while the
 * server still allows it, and its new code shown once.
 *
 * Phones hide this button (App's phone-hide), but it stays mounted, so the check still runs. What it opens by
 * itself (the code, or why it logged out) goes to the page's body: a modal inside a hidden span is invisible
 * and leaves the whole page inert.
 */
import { useState } from 'react'
import { createPortal } from 'react-dom'
import { useQuery } from '@tanstack/react-query'

import { checkAccount } from '../../lib/learner/accountCheck'
import { getProfile, takeLoggedOutNote } from '../../lib/learner/profile'

import { useRewards } from '../../lib/learner/useRewards'
import LevelRing from './LevelRing'
import LogInButton from './LogInButton'
import ProfileDialog from './ProfileDialog'
import RecoveryCode from './RecoveryCode'
import BottomSheet from '../ui/overlays/BottomSheet'

const above = (node) => createPortal(node, document.body)

export default function ProfileButton() {
  const [name] = useState(getProfile)
  const [open, setOpen] = useState(false)
  const [noted, setNoted] = useState(() => !!takeLoggedOutNote())
  const [code, setCode] = useState('')
  useQuery({ queryKey: ['account-check', name], queryFn: () => checkAccount(name, setCode), enabled: !!name, retry: false })
  const { rewards, gain } = useRewards(name)
  if (!name) {
    return (
      <span className="flex items-center gap-1.5 shrink-0">
        {/* A bare number in a ring beside Log in read as a count of something; on a wide header it is named.
            Hidden from a screen reader, which hears the ring's own "Level 1, Seed". */}
        {rewards && <span aria-hidden="true" className="type-small text-[var(--text-faint)] max-lg:hidden">Level</span>}
        <LevelRing rewards={rewards} gain={gain} />
        <LogInButton quiet />
        {noted && above(<ProfileDialog onClose={() => setNoted(false)} />)}
      </span>
    )
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        title="Your profile"
        aria-haspopup="dialog"
        dir="auto"
        className="type-small px-2 py-1 rounded-[var(--radius-sm)] border border-[var(--border)]
          text-[var(--text-dim)] hover:text-[var(--text)] max-w-[10rem] shrink-0 flex items-center gap-1.5"
      >
        <LevelRing rewards={rewards} gain={gain} />
        <span className="truncate">{name}</span>
      </button>
      {/* Mounted only while open, so each opening starts from who is logged in. */}
      {open && above(<ProfileDialog onClose={() => setOpen(false)} />)}
      {/* Held: one stray tap must not lose a code shown once; "I have saved it" is the way on. */}
      {code && above(
        <BottomSheet held label="Your recovery code" onClose={() => setCode('')} className="p-5 space-y-4">
          <p className="type-small text-[var(--text-dim)]">
            Accounts now have a recovery code, and this device has just claimed yours.
          </p>
          <RecoveryCode code={code} onDone={() => setCode('')} />
        </BottomSheet>,
      )}
    </>
  )
}
