/**
 * Your circles: invites waiting for you, the circles you are in, and a form to
 * make one. Every rule (who may invite, who sees whom, what an invite shows) is
 * the server's; this lists what it returns. Opening a circle is profile/CircleOpen.
 *
 * `run` is the one way a change goes out: it calls, then refreshes every
 * circle query, so a list never shows what the server has already changed.
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { smartError } from '../../lib/api/apiError'
import { answerInvite, createCircle, fetchCircles } from '../../lib/learner/progress'

import CircleOpen from './CircleOpen'
import SearchBox from '../ui/SearchBox'
import ErrorAlert from '../ui/ErrorAlert'
import { Skeleton } from '../ui/Skeleton'
import SmallButton from '../ui/SmallButton'
import WheelPicker from '../ui/WheelPicker'

const ALONE = ''

export default function CirclesView({ name, module }) {
  const client = useQueryClient()
  const circles = useQuery({ queryKey: ['circles', 'list', name], queryFn: fetchCircles })
  const [open, setOpen] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  /** Resolves what the call returned, or null after saying why it failed. */
  const run = async (call) => {
    setBusy(true)
    try {
      const done = await call()
      setError('')
      await client.invalidateQueries({ queryKey: ['circles'] })
      return done
    } catch (refused) {
      setError(smartError(refused, 'Could not reach the server. Try again.'))
      return null
    } finally {
      setBusy(false)
    }
  }

  if (circles.isPending) return <Skeleton className="h-16 w-full" />
  if (circles.isError) return <ErrorAlert inline title="Could not load your circles." onRetry={() => circles.refetch()} />
  const { kinds, circles: mine } = circles.data
  const invites = mine.filter((one) => one.status === 'invited')
  const joined = mine.filter((one) => one.status === 'joined')

  return (
    <section className="space-y-3">
      {invites.length > 0 && (
        <div className="space-y-2">
          <h3 className="type-small font-bold text-[var(--text-dim)]">Invites</h3>
          <ul className="space-y-1">
            {invites.map((one) => (
              <li key={one.id} className="flex flex-wrap items-center gap-x-3 gap-y-1 px-3 py-1.5 type-small text-[var(--text-dim)]">
                <span dir="auto" className="flex-1 min-w-[8rem]">
                  <span className="font-bold text-[var(--text)]">{one.name}</span> · {one.kind}, from {one.invitedBy}
                </span>
                <SmallButton disabled={busy} onClick={() => run(() => answerInvite(one.id, true))}>Accept</SmallButton>
                <SmallButton disabled={busy} onClick={() => run(() => answerInvite(one.id, false))}>Decline</SmallButton>
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="space-y-2">
        <h3 className="type-small font-bold text-[var(--text-dim)]">Your circles</h3>
        {joined.length === 0 && (
          <p className="type-small text-[var(--text-faint)]">None yet. Make one, or wait for an invite.</p>
        )}
        <ul className="space-y-1">
          {joined.map((one) => (
            <li key={one.id}>
              <button
                type="button"
                aria-expanded={open === one.id}
                onClick={() => setOpen(open === one.id ? null : one.id)}
                className={`w-full flex items-baseline gap-3 px-3 py-1.5 rounded-[var(--radius-sm)] type-small text-left
                  hover:bg-[var(--surface-hi)] ${open === one.id ? 'bg-[var(--surface-hi)]' : ''}`}
              >
                <span dir="auto" className="flex-1 truncate font-bold text-[var(--text)]">{one.name}</span>
                <span className="text-[var(--text-dim)]">{one.kind}</span>
                <span className="text-[var(--text-faint)]">{one.role}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
      {open !== null && (
        <CircleOpen key={open} id={open} name={name} module={module} run={run} busy={busy} circles={joined}
          onOpen={setOpen} onGone={() => setOpen(null)} />
      )}
      <NewCircle kinds={kinds} admin={joined.filter((one) => one.role === 'admin')} run={run} busy={busy} onMade={setOpen} />
      {error && <p role="alert" className="type-small text-[var(--danger)]">{error}</p>}
    </section>
  )
}

/** The make-a-circle form, folded away until asked for. */
function NewCircle({ kinds, admin, run, busy, onMade }) {
  const [asking, setAsking] = useState(false)
  const [typed, setTyped] = useState('')
  const [kind, setKind] = useState(kinds[0])
  const [inside, setInside] = useState(ALONE)

  const make = async () => {
    const made = await run(() => createCircle({ name: typed, kind, parent: inside === ALONE ? null : Number(inside) }))
    if (!made) return
    setTyped('')
    setAsking(false)
    onMade(made.id)
  }

  if (!asking) {
    return <SmallButton onClick={() => setAsking(true)}>New circle</SmallButton>
  }
  return (
    <div className="space-y-3 pt-2 border-t border-[var(--border)]">
      <SearchBox id="circle-name" label="Circle name" placeholder="e.g. Family" value={typed}
        onChange={setTyped} onSubmit={make} onClear={() => setTyped('')} busy={busy} />
      <WheelPicker label="Kind" options={kinds.map((one) => ({ id: one, label: one }))} value={kind} onChange={setKind} />
      {admin.length > 0 && (
        <WheelPicker label="Inside" value={inside} onChange={setInside}
          options={[{ id: ALONE, label: 'On its own' }, ...admin.map((one) => ({ id: String(one.id), label: one.name }))]} />
      )}
      <div className="flex justify-end">
        <SmallButton onClick={() => setAsking(false)}>Cancel</SmallButton>
      </div>
    </div>
  )
}
