/**
 * The level, worn quietly on the profile button: a thin ring that fills as the
 * level does, the level's number inside, and a small "+10" that rises and
 * fades when an answer earns. Nothing else on any tab changes; every tab that
 * saves its answers feeds this through lib/rewards.js on its own.
 *
 * Shown only for a logged-in name: the guest record is shared, so it has no XP.
 */
import { colorFor } from '../../theme'
import { rankOf, shareOf } from '../../lib/rewards'

const R = 8
const AROUND = 2 * Math.PI * R

/** `rewards` from lib/useRewards; `gain` the last earning still floating, or null. */
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
