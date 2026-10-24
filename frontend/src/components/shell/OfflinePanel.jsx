/**
 * Settings' offline section: whether the app itself is saved, and the packs a reader can add
 * or remove. Draws lib/shell/offline.js; every word is src/config/offline.json's.
 */
import { useEffect } from 'react'

import { coreLine, copy, getPack, loadPacks, PACKS, removePack, sizeLabel, useOffline } from '../../lib/shell/offline'
import { fill } from '../../lib/shell/homeCopy'
import SmallButton from '../ui/SmallButton'

export default function OfflinePanel() {
  const { supported, core, plan, packs } = useOffline()
  useEffect(loadPacks, [])

  return (
    <section aria-label={copy.title} className="space-y-3">
      <h3 className="type-micro uppercase tracking-[0.18em] text-[var(--text-faint)]">{copy.title}</h3>
      <p className="type-small text-[var(--text-dim)] leading-snug" aria-live="polite">
        {!supported ? copy.unsupported : core === 'ready' && plan ? coreLine(plan.coreBytes) : copy['core-saving']}
      </p>
      {supported && plan && (
        <>
          <p className="type-small text-[var(--text-faint)] leading-snug">{copy.seen}</p>
          <ul className="space-y-3">
            {PACKS.map((pack) => (
              <PackRow key={pack.id} pack={pack} bytes={plan.packs[pack.id]?.bytes ?? 0} {...packs[pack.id]} />
            ))}
          </ul>
        </>
      )}
    </section>
  )
}

function PackRow({ pack, bytes, status = 'none', done = 0, total = 0 }) {
  return (
    <li className="flex items-center justify-between gap-3">
      <span className="min-w-0 space-y-0.5">
        <span className="block text-sm font-medium text-[var(--text)]">
          {pack.label} <span className="type-small font-normal text-[var(--text-faint)] tabular-nums">· {sizeLabel(bytes)}</span>
        </span>
        <span className="block type-small text-[var(--text-faint)] leading-snug">
          {status === 'failed' ? copy.failed : pack.blurb}
        </span>
      </span>
      <span className="shrink-0 flex items-center gap-2 type-small tabular-nums" aria-live="polite">
        {status === 'getting' && <span className="text-[var(--text-dim)]">{fill(copy.getting, { done, total })}</span>}
        {status === 'ready' && (
          <>
            <span className="text-[var(--success)]">{copy.ready}</span>
            <SmallButton onClick={() => removePack(pack.id)}>{copy.remove}</SmallButton>
          </>
        )}
        {(status === 'none' || status === 'failed') && <SmallButton onClick={() => getPack(pack.id)}>{copy.get}</SmallButton>}
      </span>
    </li>
  )
}
