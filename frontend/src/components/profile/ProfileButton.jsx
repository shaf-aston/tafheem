/**
 * The header's "who is logged in": the username, or the guest's LogInButton, with the level
 * worn quietly beside it (LevelRing).
 *
 * On each load it checks the name with the server (`checkAccount`). A name the server will not
 * take from this browser (deleted in another tab, or an account this browser holds no token for)
 * logs out by itself, saying why in the log-in box, rather than every answer silently failing to
 * save. A name from before recovery codes is claimed by this browser there and then, while the
 * server still allows it, and its new code shown once.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { checkAccount } from '../../lib/learner/accountCheck'
import { getProfile, takeLoggedOutNote } from '../../lib/learner/profile'

import { useRewards } from '../../lib/learner/useRewards'
import LevelRing from './LevelRing'
import LogInButton from './LogInButton'
import ProfileDialog from './ProfileDialog'
import RecoveryCode from './RecoveryCode'
import BottomSheet from '../ui/overlays/BottomSheet'

export default function ProfileButton() {
  const [name] = useState(getProfile)
  const [open, setOpen] = useState(false)
  const [code, setCode] = useState('')
  useQuery({ queryKey: ['account-check', name], queryFn: () => checkAccount(name, setCode), enabled: !!name, retry: false })
  const { rewards, gain } = useRewards(name)
  if (!name) {
    return (
      <span className="flex items-center gap-1.5 shrink-0">
        <LevelRing rewards={rewards} gain={gain} />
        <LogInButton quiet opened={!!takeLoggedOutNote()} />
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
      {open && <ProfileDialog onClose={() => setOpen(false)} />}
      {code && (
        <BottomSheet label="Your recovery code" onClose={() => setCode('')} className="p-5 space-y-4">
          <p className="type-small text-[var(--text-dim)]">
            Accounts now have a recovery code, and this device has just claimed yours.
          </p>
          <RecoveryCode code={code} onDone={() => setCode('')} />
        </BottomSheet>
      )}
    </>
  )
}
