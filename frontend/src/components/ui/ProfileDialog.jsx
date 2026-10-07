/**
 * Type a name, get your own record. It is a name tag, not a login: the lines
 * under the box say what it does and that it has no password. The first name typed on a device may take the answers given before names
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
  const title = current ? 'Change progress name' : 'Progress name'
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
    <BottomSheet label={title} onClose={onClose} className="p-5 space-y-4">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-base font-bold text-[var(--text)]">{title}</h2>
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
        label="Progress name"
        placeholder="e.g. amina-quran"
        value={typed}
        onChange={(value) => { setTyped(value); setError('') }}
        onSubmit={save}
        onClear={() => setTyped('')}
        busy={busy}
      />
      {error && <p role="alert" className="type-small text-[var(--danger)]">{error}</p>}
      <ul className="type-small text-[var(--text-dim)] space-y-1 list-disc ps-5">
        <li>Your answers are saved under this name, apart from everyone else's.</li>
        <li>Type the same name on another device to carry on there.</li>
        <li>It is not a password: anyone who types this name sees this progress, so pick one only you would use.</li>
      </ul>

      {!current && (
        <label className="flex items-center gap-2 type-small text-[var(--text-dim)]">
          <input type="checkbox" checked={keep} onChange={(e) => setKeep(e.target.checked)} />
          Move answers already given on this device to this name
        </label>
      )}

      <PrimaryButton onClick={save} loading={busy} disabled={busy || !typed.trim()}>
        {current ? 'Change' : 'Save'}
      </PrimaryButton>
    </BottomSheet>
  )
}
