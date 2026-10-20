/** XP and streak when logged in, or the way to log in. One job: the progress line of Home. */
import XpCard from '../profile/XpCard'
import LogInButton from '../profile/LogInButton'

export default function ProgressStrip({ name, rewards, streak, copy }) {
  if (!name) {
    return (
      <p className="flex flex-wrap items-center gap-x-3 gap-y-2 text-[var(--text-dim)]">
        <span>{copy.guest}</span>
        <LogInButton>{copy['guest-go']}</LogInButton>
      </p>
    )
  }
  return (
    <div className="space-y-2">
      <XpCard rewards={rewards} />
      {streak > 0 && (
        <p className="type-small text-[var(--text-dim)]">
          {streak === 1 ? copy['streak-one'] : `${streak} ${copy['streak-many']}`}
        </p>
      )}
    </div>
  )
}
