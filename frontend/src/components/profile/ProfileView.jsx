/**
 * The logged-in profile: who, since when, how far along, the streak and each
 * module's record, your circles, and where that puts you among everyone else.
 * Words learnt is the ranking's measure because it is the one figure that
 * cannot be bought by answering a lot.
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { startOver } from '../../lib/nav/journey'
import { logOut } from '../../lib/learner/profile'
import { deleteAccount, setPublic } from '../../lib/learner/progress'
import { accountQuery, everyRanking, leaderboardQuery } from '../../lib/learner/record'
import { forgetShelf } from '../../lib/store/shelf'
import { ARMED_MS, useMoment } from '../../lib/hooks/useMoment'
import { useProgressFacts } from '../../lib/learner/useProgressFacts'

import CirclesView from './CirclesView'
import ModuleRows from './ModuleRows'
import Ranking from './Ranking'
import XpCard from './XpCard'
import LevelSetting from '../level/LevelSetting'
import ErrorAlert from '../ui/feedback/ErrorAlert'
import { Skeleton } from '../ui/feedback/Skeleton'
import SmallButton from '../ui/buttons/SmallButton'

export default function ProfileView({ name }) {
  const { module, account, overview, stats, learnt, covered, rewards } = useProgressFacts(name)

  return (
    <div className="space-y-4">
      <div dir="auto" className="text-lg font-bold text-[var(--text)] truncate">{name}</div>
      {account.isError && (
        <ErrorAlert inline title="Could not load your profile." onRetry={() => account.refetch()} />
      )}
      <LevelSetting />
      <dl className="grid grid-cols-2 gap-3">
        <XpCard rewards={rewards} />
        <Fact name="Joined" value={account.data && new Date(account.data.joined).toLocaleDateString()} />
        <Fact name="Answers given" value={account.data?.answers} />
        <Fact name="Words learnt" value={stats.data && learnt.length} />
        <Fact name="Of the Qur’an" value={covered} />
        <Fact className="col-span-2" name="Streak"
          value={overview.data && `${overview.data.streak} ${overview.data.streak === 1 ? 'day' : 'days'} in a row`} />
      </dl>
      <ModuleRows overview={overview} />
      <CirclesView name={name} module={module} />
      <Global name={name} module={module} account={account} />
      <Leave />
    </div>
  )
}

function Fact({ name, value, className = '' }) {
  return (
    <div className={`rounded-[var(--radius-sm)] border border-[var(--border)] p-3 ${className}`}>
      <dt className="type-small text-[var(--text-faint)]">{name}</dt>
      <dd className="text-lg font-bold text-[var(--text)]">
        {value ?? <Skeleton className="h-6 w-12" />}
      </dd>
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
 * Log out, then the two that cannot be undone, in their own red box: Start
 * over (progress and XP back to zero, the account kept) and Delete account.
 * Each asks twice, its first press arming it for ARMED_MS.
 */
function Leave() {
  const [asking, setAsking] = useMoment(ARMED_MS)
  const [failed, setFailed] = useState(false)

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
      <div className="flex justify-end"><SmallButton onClick={logOut}>Log out</SmallButton></div>
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
