/**
 * Home's progress column on a wide screen, in the profile's order (profile/CalmProgress): this week, then how much
 * you understand, then quieter the level, the streak and the top of the ranking, with the way into the full profile.
 * Figures from lib/learner/useProgressFacts, the same the profile shows; words from home.json `stats`.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { fill } from '../../lib/shell/homeCopy'
import { leaderboardQuery } from '../../lib/learner/record'
import { rankOf, shareOf } from '../../lib/learner/rewards'
import { useProgressFacts } from '../../lib/learner/useProgressFacts'
import { colorFor } from '../../theme'
import knobs from '../../config/home.json'

import { Fact, ThisWeek, Understanding } from '../profile/CalmProgress'
import LogInButton from '../profile/LogInButton'
import ProfileDialog from '../profile/ProfileDialog'
import Ranking from '../profile/Ranking'
import { Skeleton } from '../ui/feedback/Skeleton'
import SmallButton from '../ui/buttons/SmallButton'

const { stats: copy } = knobs
const TOP = 3

export default function StatsRail({ name }) {
  return (
    <aside aria-label={copy.title} className="space-y-4 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-4">
      {/* Logged in, "This week" heads the column; the aside keeps the title as its name. */}
      {name ? <Facts name={name} /> : (
        <>
          <h3 className="eyebrow">{copy.title}</h3>
          <p className="type-small text-[var(--text-dim)]">{copy.guest}</p>
          <LogInButton />
        </>
      )}
    </aside>
  )
}

function Facts({ name }) {
  const [open, setOpen] = useState(false)
  const { module, account, overview, stats, learnt, share, covered, rewards } = useProgressFacts(name)
  const board = useQuery(leaderboardQuery(module))
  const streak = overview.data?.streak
  return (
    <>
      <ThisWeek overview={overview} stats={stats} learnt={learnt} account={account} />
      <Understanding share={share} covered={covered} />
      <div className="calm-more space-y-4">
        <Level rewards={rewards} />
        <dl>
          <Fact name={copy.streak} value={streak !== undefined && fill(copy[streak === 1 ? 'days-one' : 'days-many'], { n: streak })} />
        </dl>
        <Ranking board={board} name={name} title={copy.board} limit={TOP} compact />
      </div>
      <SmallButton onClick={() => setOpen(true)}>{copy.open} →</SmallButton>
      {open && <ProfileDialog onClose={() => setOpen(false)} />}
    </>
  )
}

/** Level, rank and the bar to the next one: XpCard's top line, without the path. */
function Level({ rewards }) {
  if (!rewards) return <Skeleton className="h-12 w-full" />
  const rank = rankOf(rewards.level)
  return (
    <div className="space-y-2" style={{ '--xp-tone': colorFor('tab', 'grow') }}>
      <p className="type-small font-semibold text-[var(--text)]">
        {fill(copy.level, { n: rewards.level })} · {rank.en} <span dir="rtl">{rank.ar}</span>
      </p>
      <div className="xp-bar" role="progressbar" aria-valuemin={0} aria-valuemax={rewards.need} aria-valuenow={rewards.into}>
        <span style={{ '--xp-share': shareOf(rewards) }} />
      </div>
      <p className="type-small tabular-nums text-[var(--text-faint)]">
        {fill(copy['xp-left'], { n: rewards.need - rewards.into, next: rewards.level + 1 })}
      </p>
    </div>
  )
}
