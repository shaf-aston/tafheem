/**
 * Level and XP as one card, in the profile the header's level opens: a bar that
 * fills on sight, what is left to the next level, and the growth path from Seed
 * to Fruit with you on it, shown at once rather than behind a tap.
 */
import { colorFor } from '../../theme'
import config from '../../config/rewards.json'
import { rankOf, shareOf } from '../../lib/learner/rewards'
import { Skeleton } from '../ui/Skeleton'

export default function XpCard({ rewards }) {
  if (!rewards) {
    return <div className="col-span-2 rounded-[var(--radius-sm)] border border-[var(--border)] p-3"><Skeleton className="h-10 w-full" /></div>
  }
  const rank = rankOf(rewards.level)
  const share = shareOf(rewards)
  const next = config.ranks.find((r) => r.from > rewards.level)
  const tone = colorFor('tab', 'grow')
  return (
    <div
      className="xp-card col-span-2 text-start rounded-[var(--radius-sm)] border border-[var(--border)] p-3 space-y-2"
      style={{ '--xp-tone': tone }}>
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-lg font-bold text-[var(--text)]">
          Lv {rewards.level} · {rank.en} <span dir="rtl">{rank.ar}</span>
        </span>
        <span className="type-small tabular-nums text-[var(--text-dim)]">{rewards.into} / {rewards.need} XP</span>
      </div>
      <div className="xp-bar" role="progressbar" aria-valuemin={0} aria-valuemax={rewards.need} aria-valuenow={rewards.into}>
        <span style={{ '--xp-share': share }} />
      </div>
      <div className="type-small text-[var(--text-faint)]">
        {rewards.need - rewards.into} XP to level {rewards.level + 1} · {rewards.xp} XP in all
      </div>
      <ol className="xp-path" aria-label="Ranks">
        {config.ranks.map((r, i) => {
          const state = r === rank ? 'now' : r.from < rank.from ? 'done' : 'ahead'
          return (
            <li key={r.from} className={`xp-step xp-${state}`} style={{ '--i': i }}>
              <span className="xp-dot" aria-hidden="true" />
              <span className="font-semibold" dir="rtl">{r.ar}</span>
              <span className="type-small">{r.en}</span>
              <span className="type-small tabular-nums">Lv {r.from}</span>
            </li>
          )
        })}
      </ol>
      {next && (
        <div className="type-small text-[var(--text-dim)]">
          Next rank: {next.en} <span dir="rtl">{next.ar}</span> at level {next.from}
        </div>
      )}
    </div>
  )
}
