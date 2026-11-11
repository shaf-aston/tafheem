/**
 * Log in, sign up, or see your profile. No password: signing up keeps this
 * browser logged in (an HttpOnly cookie the page never sees) and hands back a
 * recovery code, shown once, which is how the account logs in anywhere else.
 * Log-in asks for that code only when the server says it needs it (a 403), so
 * a browser that is already the account's, or an account from before codes
 * being claimed, goes straight in. A first sign-up on a device may take the
 * guest answers given so far, so nothing answered is lost. The server decides
 * what a username is; a refusal (taken, no such username, wrong code) shows
 * its reason under the box.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { smartError } from '../../lib/api/apiError'
import { getProfile, logInAs, takeLoggedOutNote } from '../../lib/learner/profile'
import { fetchAccountNames, logIn, needsCode, signUp } from '../../lib/learner/progress'
import { LEVEL_KEY } from '../../lib/learner/learnerLevel'
import { copyGuestShelf, pullShelf, startShelf } from '../../lib/store/shelf'
import { readRaw } from '../../lib/store/stored'

import BottomSheet from '../ui/overlays/BottomSheet'
import SheetHeader from '../ui/overlays/SheetHeader'
import PrimaryButton from '../ui/buttons/PrimaryButton'
import ProfileView from './ProfileView'
import RecoveryCode from './RecoveryCode'
import { GuestProgress } from './CalmProgress'
import SearchBox from '../ui/inputs/SearchBox'
import Segmented from '../ui/inputs/Segmented'
import SmallButton from '../ui/buttons/SmallButton'
import LevelSetting from '../level/LevelSetting'

const MODES = [{ id: 'login', label: 'Log in' }, { id: 'signup', label: 'Sign up' }]

export default function ProfileDialog({ onClose }) {
  const name = getProfile()
  // Not "Log in or sign up": the switch right under the title says that.
  const title = name ? 'Your profile' : 'Your account'
  // While a new recovery code is on screen the sheet stays: closing it would lose a code shown once.
  const [held, setHeld] = useState(false)

  return (
    <BottomSheet held={held} label={title} onClose={onClose} className="p-5 space-y-4">
      <SheetHeader onClose={held ? () => {} : onClose} closeClassName={held ? 'invisible' : ''} className="">
        <h2 className="type-head type-lead font-bold text-[var(--text)]">{title}</h2>
      </SheetHeader>
      {/* A guest sees this device's own week first; logging in keeps it on any device. */}
      {name ? <ProfileView name={name} /> : <><GuestProgress /><SignIn onHold={setHeld} /></>}
    </BottomSheet>
  )
}

function SignIn({ onHold = () => {} }) {
  const [mode, setMode] = useState('login')
  const [typed, setTyped] = useState('')
  const [keep, setKeep] = useState(true)
  const [code, setCode] = useState('')
  const [askCode, setAskCode] = useState(false)
  // Why this browser was logged out by itself (ProfileButton), said once, where the way back in is.
  const [error, setError] = useState(takeLoggedOutNote)
  const [busy, setBusy] = useState(false)
  // A new recovery code waiting to be seen before the page reloads as the account: { code, finish }.
  const [shown, setShown] = useState(null)
  const signingUp = mode === 'signup'

  // Beta only: the server stops answering once beta_list_accounts is off, and the list goes.
  const names = useQuery({ queryKey: ['account-names'], queryFn: fetchAccountNames, retry: false })

  const go = async (chosen = typed) => {
    setBusy(true)
    try {
      const { name, recovery } = await (signingUp ? signUp(chosen, keep) : logIn(chosen, askCode ? code : ''))
      // A new name starts from the guest's shelf only if it kept the guest's answers; the level picked above goes either way.
      const fresh = () => startShelf(name, { [LEVEL_KEY]: readRaw(LEVEL_KEY) })
      const finish = async () => {
        await (signingUp ? (keep ? copyGuestShelf(name) : fresh()) : pullShelf(name))
        logInAs(name)
      }
      // The browser is logged in already (the cookie is set); the reload waits until the code has been seen.
      if (recovery) { onHold(true); setShown({ code: recovery, finish }) }
      else await finish()
    } catch (refused) {
      if (!signingUp && needsCode(refused)) setAskCode(true)
      setError(smartError(refused, 'Could not reach the server. Try again.'))
      setBusy(false)
    }
  }

  if (shown) return <RecoveryCode code={shown.code} onDone={shown.finish} />

  return (
    <>
      <Segmented fill label="Log in or sign up" options={MODES} value={mode} accent="var(--primary)"
        onChange={(next) => { setMode(next); setError(''); setAskCode(false) }} />
      <SearchBox
        id="profile-name"
        label="Username"
        placeholder="e.g. amina"
        value={typed}
        onChange={(value) => { setTyped(value); setError(''); setAskCode(false) }}
        onSubmit={() => go()}
        onClear={() => setTyped('')}
        busy={busy}
      />
      {askCode && (
        <label className="block space-y-1 type-small text-[var(--text-dim)]">
          <span>Recovery code</span>
          <input id="profile-code" value={code} dir="ltr" autoComplete="one-time-code" autoCapitalize="characters"
            spellCheck={false} placeholder="XXXX-XXXX-XXXX-XXXX" maxLength={40}
            onChange={(e) => { setCode(e.target.value); setError('') }}
            onKeyDown={(e) => { if (e.key === 'Enter' && code.trim()) go() }}
            className="w-full px-3 py-2 rounded-[var(--radius-sm)] border border-[var(--border)] bg-transparent
              font-mono tracking-wider text-[var(--text)]" />
        </label>
      )}
      {error && <p role="alert" className="type-small text-[var(--danger)]">{error}</p>}
      <p className="type-small text-[var(--text-faint)]">
        {askCode
          ? "The code was shown when you signed up, or when you last made a new one in your profile. Lost it? The site's owner can make you a new one."
          : 'No password. This device stays logged in; another device needs the recovery code you get when you sign up.'}
      </p>
      {/* Asked here, prefilled with what Home's first visit picked: the account starts at the right place. */}
      {signingUp && <LevelSetting hint={false} />}
      {signingUp && (
        <label className="flex items-center gap-2 type-small text-[var(--text-dim)]">
          <input type="checkbox" checked={keep} onChange={(e) => setKeep(e.target.checked)} />
          Move answers given on this device to my new account
        </label>
      )}
      <PrimaryButton onClick={() => go()} loading={busy} disabled={busy || !typed.trim() || (askCode && !code.trim())}>
        {signingUp ? 'Sign up' : 'Log in'}
      </PrimaryButton>
      {!signingUp && names.data?.length > 0 && (
        <div className="space-y-2">
          <p className="type-small text-[var(--text-faint)]">Beta: tap a username to log in as it.</p>
          <div className="flex flex-wrap gap-2">
            {names.data.map((one) => (
              <SmallButton key={one} dir="auto" disabled={busy} onClick={() => { setTyped(one); go(one) }}
                className="text-[var(--text-dim)]">
                {one}
              </SmallButton>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
