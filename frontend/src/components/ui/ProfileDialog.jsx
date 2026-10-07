/**
 * Type a name, get your own record. No password: the line under the box says
 * so. The first name typed on a device may take the answers given before names
 * existed, so nothing answered so far is lost. The server decides what a name
 * is; a refusal shows its reason under the box.
 */
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { smartError } from '../../lib/apiError'
import { getProfile, readsProgress, setProfile } from '../../lib/profile'
import { startProfile } from '../../lib/progress'

import BottomSheet from './BottomSheet'
import PrimaryButton from './PrimaryButton'
import SearchBox from './SearchBox'

export default function ProfileDialog({ onClose, onSaved }) {
  const client = useQueryClient()
  const current = getProfile()
  const [typed, setTyped] = useState(current)
  const [keep, setKeep] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const save = async () => {
    setBusy(true)
    try {
      const { name } = await startProfile(typed, !current && keep)
      setProfile(name)
      // Every progress answer on screen belonged to the old name.
      await client.invalidateQueries({ predicate: readsProgress })
      onSaved(name)
      onClose()
    } catch (refused) {
      setError(smartError(refused, 'Could not save the name. Try again.'))
      setBusy(false)
    }
  }

  return (
    <BottomSheet label={current ? 'Switch name' : "Who's learning?"} onClose={onClose} className="p-5 space-y-4">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-base font-bold text-[var(--text)]">{current ? 'Switch name' : "Who's learning?"}</h2>
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
    </BottomSheet>
  )
}
