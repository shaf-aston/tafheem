/**
 * The header's "who is logged in": the username, or the guest's LogInButton, with the level
 * worn quietly beside it (LevelRing). A username the
 * server no longer knows (deleted in another tab) logs out by itself, rather
 * than every answer silently failing to save.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getProfile, logOut } from '../../lib/learner/profile'
import { fetchAccount } from '../../lib/learner/progress'

import { useRewards } from '../../lib/learner/useRewards'
import LevelRing from './LevelRing'
import LogInButton from './LogInButton'
import ProfileDialog from './ProfileDialog'

export default function ProfileButton() {
  const [name] = useState(getProfile)
  const [open, setOpen] = useState(false)
  const check = () => fetchAccount().catch((error) => {
    if (error.response?.status !== 401) throw error
    logOut()
    return null
  })
  useQuery({ queryKey: ['account-check', name], queryFn: check, enabled: !!name, retry: false })
  const { rewards, gain } = useRewards(name)
  if (!name) return <LogInButton quiet />

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
    </>
  )
}
