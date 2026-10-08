/**
 * The logged-in profile: who, since when, how far along, and where that puts
 * you among everyone else. Words learnt is the leaderboard's measure because
 * it is the one figure that cannot be bought by answering a lot.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { shareOf } from '../../lib/coverage'
import { logOut } from '../../lib/profile'
import { deleteAccount, fetchAccount, fetchLeaderboard } from '../../lib/progress'
import { moduleFor, QUIZ } from '../../lib/quizBanks'
import { forgetShelf } from '../../lib/shelf'
import { useQuizCoverage } from '../../lib/useQuizCoverage'

import { Skeleton } from './Skeleton'
import SmallButton from './SmallButton'

export default function ProfileView({ name, onLeave }) {
  const language = QUIZ.language
  const module = moduleFor(language)
  const account = useQuery({ queryKey: ['account', name], queryFn: fetchAccount })
  const { stats, learnt, share } = useQuizCoverage(language)
  const board = useQuery({ queryKey: ['leaderboard', module], queryFn: () => fetchLeaderboard(module) })
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
      </dl>
      <Board board={board} name={name} />
      <Leave onLeave={onLeave} />
    </div>
  )
}

function Fact({ name, value }) {
  return (
    <div className="rounded-[var(--radius-sm)] border border-[var(--border)] p-3">
      <dt className="type-small text-[var(--text-faint)]">{name}</dt>
      <dd className="text-lg font-bold text-[var(--text)]">
        {value ?? <Skeleton className="h-6 w-12" />}
      </dd>
    </div>
  )
}

/** The top accounts by words learnt; your row stands out, and is added below when not in the top. */
function Board({ board, name }) {
  if (board.isPending) return <Skeleton className="h-24 w-full" />
  if (board.isError) return <p className="type-small text-[var(--danger)]">Could not load the leaderboard.</p>
  const { rows, you } = board.data
  const shown = you && !rows.some((row) => row.name === name) ? [...rows, you] : rows
  return (
    <section className="space-y-2">
      <h3 className="type-small font-bold text-[var(--text-dim)]">Leaderboard: words learnt</h3>
      <ol className="space-y-1">
        {shown.map((row) => {
          const mine = row.name === name
          return (
            <li
              key={row.name}
              className={`flex items-center gap-3 px-3 py-1.5 rounded-[var(--radius-sm)] type-small ${
                mine ? 'bg-[var(--surface-hi)] font-bold text-[var(--gold)]' : 'text-[var(--text-dim)]'}`}
            >
              <span className="w-6 tabular-nums">{row.rank}</span>
              <span dir="auto" className="flex-1 truncate">{mine ? `${row.name} (you)` : row.name}</span>
              <span className="tabular-nums">{row.learnt}</span>
            </li>
          )
        })}
      </ol>
    </section>
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
