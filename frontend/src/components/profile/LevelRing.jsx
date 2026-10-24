/**
 * The level on the profile button: a thin ring, the number inside, a fading "+10".
 * A guest wears one too, for their device's XP (docs/plans/2026-10-24-device-guest.md §8).
 */
import { colorFor } from '../../theme'
import { rankOf, shareOf } from '../../lib/learner/rewards'

const R = 8
const AROUND = 2 * Math.PI * R

/** `rewards` and `gain` from lib/learner/useRewards. */
export default function LevelRing({ rewards, gain }) {
  if (!rewards) return null
  const rank = rankOf(rewards.level)
  const filled = shareOf(rewards) * AROUND
  return (
    <span className="level-ring" title={`${rank.en} · level ${rewards.level} · ${rewards.into} / ${rewards.need} XP`}>
      <svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true">
        <circle cx="10" cy="10" r={R} fill="none" stroke="var(--border)" strokeWidth="2" />
        <circle cx="10" cy="10" r={R} fill="none" stroke={colorFor('tab', 'grow')} strokeWidth="2" strokeLinecap="round"
          strokeDasharray={`${filled} ${AROUND}`} transform="rotate(-90 10 10)" className="level-ring-fill" />
      </svg>
      <span className="level-ring-n">{rewards.level}</span>
      <span className="sr-only">Level {rewards.level}, {rank.en}</span>
      {gain && <span key={gain.at} className="level-ring-gain" aria-hidden="true">+{gain.n}</span>}
    </span>
  )
}
