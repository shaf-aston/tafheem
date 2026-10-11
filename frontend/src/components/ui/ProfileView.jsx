/**
 * The logged-in profile: who, since when, how far along, the streak and each
 * module's record, your circles, and where that puts you among everyone else.
 * Words learnt is the ranking's measure because it is the one figure that
 * cannot be bought by answering a lot.
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { shareOf } from '../../lib/coverage'
import { logOut } from '../../lib/profile'
import { deleteAccount, fetchAccount, fetchLeaderboard, fetchOverview, setPublic } from '../../lib/progress'
import { MEANINGS } from '../../lib/quiz'
import { moduleFor, QUIZ } from '../../lib/quizBanks'
import { forgetShelf } from '../../lib/shelf'
import { useQuizCoverage } from '../../lib/useQuizCoverage'
import { useRemembered } from '../../lib/useRemembered'

import CirclesView from './CirclesView'
import ModuleRows from './ModuleRows'
import Ranking from './Ranking'
import { Skeleton } from './Skeleton'
import SmallButton from './SmallButton'

export default function ProfileView({ name, onLeave }) {
  // The language the quiz was last set to, as the quiz reads it: an Urdu
  // learner's words are filed under the Urdu module, not the default's.
  const [language] = useRemembered('quiz-language', Object.keys(MEANINGS), QUIZ.language)
  const module = moduleFor(language)
  const account = useQuery({ queryKey: ['account', name], queryFn: fetchAccount })
  const { stats, learnt, share } = useQuizCoverage(language)
  const overview = useQuery({ queryKey: ['overview', name], queryFn: fetchOverview })
  // Nothing learnt covers nothing; something learnt waits for the word table.
  const covered = !stats.data ? null : learnt.length === 0 ? '0%' : share === null ? null : `${shareOf(share, language)}%`

  return (
    <div className="space-y-4">
      <div dir="auto" className="text-lg font-bold text-[var(--text)] truncate">{name}</div>
      {account.isError && (
        <p role="alert" className="type-small text-[var(--danger)]">Could not load your profile.</p>
      )}
      <dl className="grid grid-cols-2 gap-3">
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
      <Leave onLeave={onLeave} />
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
  const board = useQuery({ queryKey: ['leaderboard', module], queryFn: () => fetchLeaderboard(module) })
  const toggle = async (shown) => {
    client.setQueryData(['account', name], await setPublic(shown))
    await client.invalidateQueries({ queryKey: ['leaderboard'] })
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

/** Log out, or delete the account: the second asks twice, since it cannot be undone. */
function Leave({ onLeave }) {
  const [asking, setAsking] = useState(false)
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
    onLeave()
  }

  return (
    <div className="pt-2 border-t border-[var(--border)] space-y-2">
      <div className="flex items-center justify-end gap-2">
        <SmallButton onClick={() => { logOut(); onLeave() }}>Log out</SmallButton>
        <SmallButton
          className={asking ? 'text-[var(--danger)] border-[var(--danger)]' : ''}
          onClick={() => (asking ? remove() : setAsking(true))}
        >
          {asking ? 'Sure? Delete it all' : 'Delete account'}
        </SmallButton>
      </div>
      {asking && (
        <p aria-live="polite" className="type-small text-[var(--text-faint)]">
          {failed ? 'Could not delete. Try again.' : 'Deletes your username, every answer you gave and your saved settings.'}
        </p>
      )}
    </div>
  )
}
