/**
 * Your team: everyone under you, branching down (a member with members of its
 * own opens into theirs), each with words learnt and answers given. Any account
 * becomes a team by adding a member. The tree, and every rule about who may
 * join or leave, comes from the server (GET/POST/DELETE /api/progress/team).
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { smartError } from '../../lib/apiError'
import { addMember, fetchTeam, removeMember } from '../../lib/progress'

import { Skeleton } from './Skeleton'
import SearchBox from './SearchBox'
import SmallButton from './SmallButton'

export default function TeamView({ name, module }) {
  const client = useQueryClient()
  const key = ['team', name, module]
  const team = useQuery({ queryKey: key, queryFn: () => fetchTeam(module) })
  const [typed, setTyped] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  // Each change answers with the new team, so the tree updates without asking again.
  const change = async (call) => {
    setBusy(true)
    try {
      client.setQueryData(key, await call())
      setError('')
      return true
    } catch (refused) {
      setError(smartError(refused, 'Could not reach the server. Try again.'))
      return false
    } finally {
      setBusy(false)
    }
  }
  const add = async () => {
    if (await change(() => addMember(typed, module))) setTyped('')
  }

  if (team.isPending) return <Skeleton className="h-16 w-full" />
  if (team.isError) return <p className="type-small text-[var(--danger)]">Could not load your team.</p>
  const { tree, teams } = team.data

  return (
    <section className="space-y-2">
      <h3 className="type-small font-bold text-[var(--text-dim)]">Your team</h3>
      {tree.members.length === 0 ? (
        <p className="type-small text-[var(--text-faint)]">
          Add a username to follow their progress. They become your team.
        </p>
      ) : (
        <Branch members={tree.members} onRemove={(member) => change(() => removeMember(name, member, module))} busy={busy} />
      )}
      <SearchBox
        id="team-member"
        label="Add a member"
        placeholder="Add a member by username"
        value={typed}
        onChange={(value) => { setTyped(value); setError('') }}
        onSubmit={add}
        onClear={() => setTyped('')}
        busy={busy}
      />
      {error && <p role="alert" className="type-small text-[var(--danger)]">{error}</p>}
      {teams.map((above) => (
        <div key={above} className="flex items-center justify-between gap-2 type-small text-[var(--text-dim)]">
          <span dir="auto" className="truncate">In the team of {above}</span>
          <SmallButton disabled={busy} onClick={() => change(() => removeMember(above, name, module))}>Leave</SmallButton>
        </div>
      ))}
    </section>
  )
}

/**
 * One level of the tree. The line down the left joins a team to its members;
 * only your own direct members can be removed from here, theirs are theirs.
 */
function Branch({ members, onRemove, busy, depth = 0 }) {
  return (
    <ul className={depth ? 'ms-3 ps-3 border-s border-[var(--border)] space-y-1' : 'space-y-1'}>
      {members.map((member) => (
        <li key={member.name} className="space-y-1">
          <div className="flex items-center gap-3 px-3 py-1.5 rounded-[var(--radius-sm)] border border-[var(--border)] type-small">
            <span dir="auto" className="flex-1 truncate text-[var(--text)]">{member.name}</span>
            <span className="tabular-nums text-[var(--text-dim)]" title="Words learnt">{member.learnt} learnt</span>
            <span className="tabular-nums text-[var(--text-faint)]" title="Answers given">{member.answers} answers</span>
            {onRemove && (
              <SmallButton disabled={busy} onClick={() => onRemove(member.name)} aria-label={`Remove ${member.name}`}>
                Remove
              </SmallButton>
            )}
          </div>
          {member.members.length > 0 && <Branch members={member.members} depth={depth + 1} busy={busy} />}
        </li>
      ))}
    </ul>
  )
}
