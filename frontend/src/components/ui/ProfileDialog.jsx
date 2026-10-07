/**
 * Log in, sign up, or see your profile. Usernames only, no password: the line
 * under the box says so. A first sign-up on a device may take the guest answers
 * given so far, so nothing answered is lost. The server decides what a username
 * is; a refusal (taken, no such username) shows its reason under the box.
 */
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { smartError } from '../../lib/apiError'
import { getProfile, readsProgress, setProfile } from '../../lib/profile'
import { logIn, signUp } from '../../lib/progress'

import BottomSheet from './BottomSheet'
import PrimaryButton from './PrimaryButton'
import ProfileView from './ProfileView'
import SearchBox from './SearchBox'
import Segmented from './Segmented'

const MODES = [{ id: 'login', label: 'Log in' }, { id: 'signup', label: 'Sign up' }]

export default function ProfileDialog({ onClose, onSaved }) {
  const client = useQueryClient()
  const name = getProfile()
  const title = name ? 'Your profile' : 'Log in or sign up'

  // Close first: the profile's own queries would refetch as the wrong user.
  // Then every progress answer on screen, which belonged to the user before.
  const switched = (next) => {
    onSaved(next)
    onClose()
    client.invalidateQueries({ predicate: readsProgress })
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
      {name ? <ProfileView name={name} onLeave={() => switched('')} /> : <SignIn onIn={switched} />}
    </BottomSheet>
  )
}

function SignIn({ onIn }) {
  const [mode, setMode] = useState('login')
  const [typed, setTyped] = useState('')
  const [keep, setKeep] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const signingUp = mode === 'signup'

  const go = async () => {
    setBusy(true)
    try {
      const { name } = await (signingUp ? signUp(typed, keep) : logIn(typed))
      setProfile(name)
      onIn(name)
    } catch (refused) {
      setError(smartError(refused, 'Could not reach the server. Try again.'))
      setBusy(false)
    }
  }

  return (
    <>
      <Segmented label="Log in or sign up" options={MODES} value={mode} accent="var(--gold)"
        onChange={(next) => { setMode(next); setError('') }} />
      <SearchBox
        id="profile-name"
        label="Username"
        placeholder="e.g. amina"
        value={typed}
        onChange={(value) => { setTyped(value); setError('') }}
        onSubmit={go}
        onClear={() => setTyped('')}
        busy={busy}
      />
      {error && <p role="alert" className="type-small text-[var(--danger)]">{error}</p>}
      <p className="type-small text-[var(--text-faint)]">
        No password: anyone who knows your username can open your progress.
      </p>
      {signingUp && (
        <label className="flex items-center gap-2 type-small text-[var(--text-dim)]">
          <input type="checkbox" checked={keep} onChange={(e) => setKeep(e.target.checked)} />
          Move answers given on this device to my new account
        </label>
      )}
      <PrimaryButton onClick={go} loading={busy} disabled={busy || !typed.trim()}>
        {signingUp ? 'Sign up' : 'Log in'}
      </PrimaryButton>
    </>
  )
}
