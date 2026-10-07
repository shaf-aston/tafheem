/**
 * Type a name, get your own record. No password: the line under the box says
 * so. The first name typed on a device may take the answers given before names
 * existed, so nothing answered so far is lost.
 */
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { useModal } from '../../lib/useModal'
import { cleanName, getProfile, setProfile } from '../../lib/profile'
import { claimProgress } from '../../lib/progress'

import PrimaryButton from './PrimaryButton'
import SearchBox from './SearchBox'

export default function ProfileDialog({ open, onClose, onSaved }) {
  const dialog = useModal(open)
  const client = useQueryClient()
  const current = getProfile()
  const [typed, setTyped] = useState(current)
  const [keep, setKeep] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const save = async () => {
    const { name, error: wrong } = cleanName(typed)
    if (wrong) return setError(wrong)
    setBusy(true)
    setProfile(name)
    if (!current && keep) await claimProgress()
    // Every progress answer on screen belonged to the old name.
    await client.invalidateQueries()
    setBusy(false)
    setError('')
    onSaved(name)
    onClose()
  }

  return (
    <dialog
      ref={dialog}
      onClose={onClose}
      onClick={(e) => e.target === dialog.current && onClose()}
      aria-labelledby="profile-title"
      className="m-auto p-0 bg-transparent max-w-[min(var(--sheet-narrow),92vw)] w-full"
    >
      <div
        className="rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)] p-5 space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-baseline justify-between gap-3">
          <h2 id="profile-title" className="text-base font-bold text-[var(--text)]">
            {current ? 'Switch name' : "Who's learning?"}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="type-small text-[var(--text-faint)] hover:text-[var(--text)] transition-colors"
          >
            Close
          </button>
        </div>

        <SearchBox
          id="profile-name"
          label="Your name"
          placeholder="e.g. Amina"
          value={typed}
          onChange={(value) => { setTyped(value); setError('') }}
          onSubmit={save}
          onClear={() => setTyped('')}
          busy={busy}
        />
        {error && <p role="alert" className="type-small text-[var(--danger)]">{error}</p>}
        <p className="type-small text-[var(--text-faint)]">Anyone using this name sees this progress.</p>

        {!current && (
          <label className="flex items-center gap-2 type-small text-[var(--text-dim)]">
            <input type="checkbox" checked={keep} onChange={(e) => setKeep(e.target.checked)} />
            Keep progress from this device
          </label>
        )}

        <PrimaryButton onClick={save} loading={busy} disabled={busy || !typed.trim()}>
          {current ? 'Switch' : 'Save'}
        </PrimaryButton>
      </div>
    </dialog>
  )
}
