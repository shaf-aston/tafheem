/**
 * The logged-in profile, calm on top and more as you go down: this week in one
 * card, then how much you understand, then the level, the streak, each module's
 * record, your circles and where that puts you among everyone else. Words learnt
 * is the ranking's measure because it is the one figure that cannot be bought by
 * answering a lot.
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { errorMessage } from '../../lib/api/apiError'
import { startOver } from '../../lib/nav/journey'
import { logOut } from '../../lib/learner/profile'
import { deleteAccount, logOutHere, logOutOthers, needsCode, newRecoveryCode, setPublic } from '../../lib/learner/progress'
import { accountQuery, everyRanking, leaderboardQuery } from '../../lib/learner/record'
import { forgetShelf } from '../../lib/store/shelf'
import { ARMED_MS, useMoment } from '../../lib/hooks/useMoment'
import { useProgressFacts } from '../../lib/learner/useProgressFacts'

import { Fact, ThisWeek, Understanding } from './CalmProgress'
import CirclesView from './CirclesView'
import ModuleRows from './ModuleRows'
import Ranking from './Ranking'
import RecoveryCode from './RecoveryCode'
import XpCard from './XpCard'
import LevelSetting from '../level/LevelSetting'
import ErrorAlert from '../ui/feedback/ErrorAlert'
import SmallButton from '../ui/buttons/SmallButton'

export default function ProfileView({ name }) {
  const { module, account, overview, stats, learnt, share, covered, rewards } = useProgressFacts(name)
  const streak = overview.data?.streak

  return (
    <div className="space-y-4">
      <div dir="auto" className="type-heading font-bold text-[var(--text)] truncate">{name}</div>
      {account.isError && (
        <ErrorAlert inline title="Could not load your profile." onRetry={() => account.refetch()} />
      )}
      <div className="card"><ThisWeek overview={overview} stats={stats} learnt={learnt} /></div>
      <Understanding share={share} covered={covered} />
      <LevelSetting />
      <div className="calm-more space-y-4">
        <XpCard rewards={rewards} />
        <dl>
          <Fact name="Days in a row" value={streak !== undefined && `${streak} ${streak === 1 ? 'day' : 'days'}`} />
          <Fact name="Joined" value={account.data && new Date(account.data.joined).toLocaleDateString()} />
        </dl>
        <ModuleRows overview={overview} />
        <CirclesView name={name} module={module} />
        <Global name={name} module={module} account={account} />
      </div>
      <Devices />
      <Leave />
    </div>
  )
}

/** The global ranking, with the switch that takes you out of it (you still see your own row). */
function Global({ name, module, account }) {
  const client = useQueryClient()
  const board = useQuery(leaderboardQuery(module))
  const toggle = async (shown) => {
    client.setQueryData(accountQuery(name).queryKey, await setPublic(shown))
    await client.invalidateQueries(everyRanking)
  }
  return (
    <div className="space-y-2">
      <Ranking board={board} name={name} title="Global ranking: words learnt" />
      <label className="flex items-center gap-2 type-small text-[var(--text-dim)]">
        <input type="checkbox" checked={account.data?.public ?? true} disabled={!account.data}
          onChange={(e) => toggle(e.target.checked)} />
        Show me in the global ranking
      </label>
    </div>
  )
}

/**
 * This account's way in on other devices: a new recovery code (the old one stops working; shown once, here),
 * and logging every other device out, for a phone lost or lent. Each says what happened, or that it failed.
 */
function Devices() {
  const [code, setCode] = useState('')
  const [said, setSaid] = useState('')
  const [busy, setBusy] = useState(false)
  // The current code, asked for once the server says this device logged in too long ago to skip it.
  const [current, setCurrent] = useState(null)
  const act = async (work) => {
    setBusy(true)
    setSaid('')
    try {
      await work()
    } catch (refused) {
      if (needsCode(refused)) {
        setCurrent((typed) => typed ?? '')
        setSaid(errorMessage(refused))
      } else {
        setSaid('Could not reach the server. Try again.')
      }
    }
    setBusy(false)
  }
  const fresh = () => act(async () => {
    setCode(await newRecoveryCode(current))
    setCurrent(null)
  })
  const others = () => act(async () => {
    const gone = await logOutOthers()
    setSaid(gone ? `Logged out ${gone} other ${gone === 1 ? 'device' : 'devices'}.` : 'No other device was logged in.')
  })
  return (
    <section aria-labelledby="devices-title" className="space-y-2">
      <h3 id="devices-title" className="type-small font-semibold text-[var(--text)]">Other devices</h3>
      <p className="type-small text-[var(--text-faint)]">
        To log in on another device you type your recovery code there. Lost it, or someone saw it? Make a new one.
      </p>
      {code && <RecoveryCode code={code} />}
      {current !== null && (
        <label className="block space-y-1 type-small text-[var(--text-dim)]">
          <span>Current recovery code</span>
          <input value={current} dir="ltr" autoComplete="one-time-code" autoCapitalize="characters" spellCheck={false}
            placeholder="XXXX-XXXX-XXXX-XXXX" maxLength={40} onChange={(e) => setCurrent(e.target.value)}
            className="w-full px-3 py-2 rounded-[var(--radius-sm)] border border-[var(--border)] bg-transparent
              font-mono tracking-wider text-[var(--text)]" />
          <span className="block text-[var(--text-faint)]">Lost it? The site&apos;s owner can make you a new one.</span>
        </label>
      )}
      <div className="flex flex-wrap gap-2">
        <SmallButton disabled={busy || current === ''} onClick={fresh}>New recovery code</SmallButton>
        <SmallButton disabled={busy} onClick={others}>Log out other devices</SmallButton>
      </div>
      <p aria-live="polite" className="type-small text-[var(--text-dim)]">{said}</p>
    </section>
  )
}

/**
 * Log out, then the two that cannot be undone, in their own red box: Start
 * over (progress and XP back to zero, the account kept) and Delete account.
 * Each asks twice, its first press arming it for ARMED_MS.
 */
function Leave() {
  const [asking, setAsking] = useMoment(ARMED_MS)
  const [failed, setFailed] = useState(false)
  const [stuck, setStuck] = useState(false)

  // A 401 means this browser's cookie opens nothing any more: nothing is left to fear, so log out here too.
  const leave = async () => {
    try {
      await logOutHere()
    } catch (error) {
      if (error.response?.status === 401) logOut()
      else setStuck(true)
    }
  }
  const remove = async () => {
    try {
      await deleteAccount()
    } catch {
      setFailed(true)
      return
    }
    forgetShelf()
    logOut()
  }
  const risky = [
    { id: 'startOver', label: 'Start over', sure: 'Sure? Start over', act: startOver,
      says: 'Forgets where you have been, your recent searches, your answers and your Grow steps. XP goes back to zero.' },
    { id: 'delete', label: 'Delete account', sure: 'Sure? Delete it all', act: remove,
      says: failed ? 'Could not delete. Try again.' : 'Deletes your username, every answer you gave and your saved settings.' },
  ]
  const armed = risky.find((r) => r.id === asking)

  return (
    <div className="pt-2 border-t border-[var(--border)] space-y-3">
      <div className="flex justify-end"><SmallButton onClick={leave}>Log out</SmallButton></div>
      {stuck && (
        <p role="alert" className="type-small text-[var(--danger)] text-end">
          Not logged out: the server did not hear it, and this device would still let your username in. Try again
          when online.
        </p>
      )}
      <section aria-labelledby="danger-title" className="rounded-[var(--radius-md)] border border-[var(--danger-edge)] p-3 space-y-2">
        <h3 id="danger-title" className="type-small font-semibold text-[var(--danger)]">Danger zone</h3>
        <div className="flex flex-wrap justify-end gap-2">
          {risky.map((r) => (
            <SmallButton
              key={r.id}
              className={`text-[var(--danger)] ${asking === r.id ? 'border-[var(--danger)]' : ''}`}
              onClick={() => (asking === r.id ? r.act() : setAsking(r.id))}
            >
              {asking === r.id ? r.sure : r.label}
            </SmallButton>
          ))}
        </div>
        <p aria-live="polite" className="type-small text-[var(--text-faint)]">
          {armed ? armed.says : 'Neither can be undone.'}
        </p>
      </section>
    </div>
  )
}
