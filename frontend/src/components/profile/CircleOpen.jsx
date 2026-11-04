/**
 * One circle, opened: its ranking, its people (as many as the server shows
 * you), and for an admin the invite box, role changes and removal. Tapping a
 * person the server marks `seeable` opens their overview; the same rows the
 * profile shows for you (profile/ModuleRows).
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import {
  deleteCircle, fetchCircle, fetchLeaderboard, fetchMemberOverview, inviteMember, leaveCircle, moveCircle, removeMember,
  setRole,
} from '../../lib/learner/progress'

import ModuleRows from './ModuleRows'
import Ranking from './Ranking'
import SearchBox from '../ui/inputs/SearchBox'
import Segmented from '../ui/inputs/Segmented'
import ErrorAlert from '../ui/feedback/ErrorAlert'
import { Skeleton } from '../ui/feedback/Skeleton'
import SmallButton from '../ui/buttons/SmallButton'
import WheelPicker from '../ui/inputs/WheelPicker'

const ROLES = [{ id: 'member', label: 'Member' }, { id: 'admin', label: 'Admin' }]

const ALONE = ''

/** `circles` is every circle I have joined (CirclesView's list), which is where "Inside" gets its choices. */
export default function CircleOpen({ id, name, module, run, busy, circles, onOpen, onGone }) {
  const detail = useQuery({ queryKey: ['circles', 'one', id], queryFn: () => fetchCircle(id), retry: false })
  const joined = !!detail.data?.role
  const board = useQuery({
    queryKey: ['circles', 'ranking', id, module], queryFn: () => fetchLeaderboard(module, id), enabled: joined, retry: false,
  })
  const [seeing, setSeeing] = useState(null)
  const [typed, setTyped] = useState('')
  const [role, setInviteRole] = useState('member')
  const [asking, setAsking] = useState(false)

  if (detail.isPending) return <Skeleton className="h-24 w-full" />
  if (detail.isError) return <ErrorAlert inline title="Could not open this circle." onRetry={() => detail.refetch()} />
  const { members, inside, kind, parent } = detail.data
  const admin = detail.data.role === 'admin'

  // Where it may go: on its own, or in a circle I admin that is not this one nor, as far as I know, inside it.
  const shut = new Set([id, ...inside.map((one) => one.id)])
  for (let grew = true; grew;) {
    grew = false
    for (const one of circles) if (shut.has(one.parent) && !shut.has(one.id)) { shut.add(one.id); grew = true }
  }
  const homes = [
    { id: ALONE, label: 'On its own' },
    ...circles.filter((one) => one.role === 'admin' && !shut.has(one.id)).map((one) => ({ id: String(one.id), label: one.name })),
  ]
  if (parent != null && !homes.some((one) => one.id === String(parent))) homes.push({ id: String(parent), label: 'Another circle' })

  const invite = async () => {
    if (await run(() => inviteMember(id, typed, role))) setTyped('')
  }
  const leaving = async (call) => {
    if (await run(call)) onGone()
  }

  return (
    <div className="space-y-3 rounded-[var(--radius-sm)] border border-[var(--border)] p-3">
      <div className="flex items-baseline gap-3">
        <h3 dir="auto" className="flex-1 truncate type-ui font-bold text-[var(--text)]">{detail.data.name}</h3>
        <span className="type-small text-[var(--text-dim)]">{kind}</span>
      </div>
      {joined && <Ranking board={board} name={name} title="Ranking: words learnt" />}
      <ul className="space-y-1">
        {members.map((one) => (
          <li key={one.name} className="flex flex-wrap items-center gap-x-3 gap-y-1 px-3 py-1 type-small text-[var(--text-dim)]">
            {one.seeable ? (
              <button type="button" dir="auto" aria-expanded={seeing === one.name}
                onClick={() => setSeeing(seeing === one.name ? null : one.name)}
                className="flex-1 min-w-[6rem] truncate text-left font-bold text-[var(--text)] underline-offset-2 hover:underline">
                {one.name}
              </button>
            ) : (
              <span dir="auto" className="flex-1 min-w-[6rem] truncate">{one.name}</span>
            )}
            <span className="text-[var(--text-faint)]">{one.status === 'invited' ? `invited as ${one.role}` : one.role}</span>
            {admin && one.name !== name && (
              <>
                {one.status === 'joined' && (
                  <SmallButton disabled={busy}
                    onClick={() => run(() => setRole(id, one.name, one.role === 'admin' ? 'member' : 'admin'))}>
                    {one.role === 'admin' ? 'Make member' : 'Make admin'}
                  </SmallButton>
                )}
                <SmallButton disabled={busy} onClick={() => run(() => removeMember(id, one.name))}>Remove</SmallButton>
              </>
            )}
            {seeing === one.name && <div className="basis-full"><MemberOverview id={id} member={one.name} /></div>}
          </li>
        ))}
      </ul>
      {inside.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="type-small text-[var(--text-faint)]">Inside it:</span>
          {inside.map((one) => (
            <SmallButton key={one.id} dir="auto" onClick={() => onOpen(one.id)}>{one.name} · {one.kind}</SmallButton>
          ))}
        </div>
      )}
      {admin && (
        <div className="space-y-2">
          <SearchBox id={`circle-invite-${id}`} label="Invite" placeholder="Invite by username" value={typed}
            onChange={setTyped} onSubmit={invite} onClear={() => setTyped('')} busy={busy} />
          <Segmented label="Invite as" options={ROLES} value={role} onChange={setInviteRole} compact />
          <div className="flex items-center gap-3">
            <span className="type-small text-[var(--text-faint)]">Inside</span>
            <WheelPicker label="Inside" value={parent == null ? ALONE : String(parent)} disabled={busy} className="flex-1"
              onChange={(to) => run(() => moveCircle(id, to === ALONE ? null : Number(to)))} options={homes} />
          </div>
        </div>
      )}
      {joined && (
        <div className="flex items-center justify-end gap-2 pt-2 border-t border-[var(--border)]">
          <SmallButton disabled={busy} onClick={() => leaving(() => leaveCircle(id))}>Leave</SmallButton>
          {admin && (
            <SmallButton disabled={busy}
              className={asking ? 'text-[var(--danger)] border-[var(--danger)]' : ''}
              onClick={() => (asking ? leaving(() => deleteCircle(id)) : setAsking(true))}>
              {asking ? 'Sure? Delete it' : 'Delete circle'}
            </SmallButton>
          )}
        </div>
      )}
    </div>
  )
}

/** The streak and module rows of one member, as the profile shows your own. */
function MemberOverview({ id, member }) {
  const overview = useQuery({
    queryKey: ['circles', 'member', id, member], queryFn: () => fetchMemberOverview(id, member), retry: false,
  })
  const streak = overview.data?.streak
  return (
    <div className="space-y-2 py-2">
      <h4 dir="auto" className="type-small font-bold text-[var(--text)]">Progress of {member}</h4>
      {streak != null && (
        <p className="type-small text-[var(--text-dim)]">{streak} {streak === 1 ? 'day' : 'days'} in a row</p>
      )}
      <ModuleRows overview={overview} />
    </div>
  )
}
