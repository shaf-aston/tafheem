/**
 * The header's "who is logged in": the username, or Log in. A username the
 * server no longer knows (deleted in another tab) logs out by itself, rather
 * than every answer silently failing to save.
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { getProfile, logOut, readsProgress } from '../../lib/profile'
import { fetchAccount } from '../../lib/progress'

import ProfileDialog from './ProfileDialog'

export default function ProfileButton() {
  const client = useQueryClient()
  const [name, setName] = useState(getProfile)
  const [open, setOpen] = useState(false)
  const check = () => fetchAccount().catch((error) => {
    if (error.response?.status !== 401) throw error
    logOut()
    setName('')
    client.invalidateQueries({ predicate: readsProgress })
    return null
  })
  useQuery({ queryKey: ['account-check', name], queryFn: check, enabled: !!name, retry: false })

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        title={name ? 'Your profile' : 'Log in to keep your progress on any device'}
        aria-haspopup="dialog"
        dir="auto"
        className="type-small px-2 py-1 rounded-[var(--radius-sm)] border border-[var(--border)]
          text-[var(--text-dim)] hover:text-[var(--text)] max-w-[8rem] truncate shrink-0"
      >
        {name || 'Log in'}
      </button>
      {/* Mounted only while open, so each opening starts from who is logged in. */}
      {open && <ProfileDialog onClose={() => setOpen(false)} onSaved={setName} />}
    </>
  )
}
