/**
 * XP and level on the page: the learner's clock, the level names, and the one
 * place a saved answer tells the header what it earned.
 *
 * The counting is the server's (backend/services/rewards.py); this only names
 * and announces. Any tab that saves its answers through lib/progress.js earns
 * XP with no change of its own: recordAttempt hands each saved answer to
 * `announce`, and whoever listens (the profile button) shows it.
 */
import config from '../rewards.json'

/** Minutes east of UTC on this device, so "once a day" is the learner's own day. */
export const tz = (now = new Date()) => -now.getTimezoneOffset() || 0

const listeners = new Set()

/** Hear every saved answer that came back with rewards. Returns the unsubscribe. */
export function onEarned(listen) {
  listeners.add(listen)
  return () => listeners.delete(listen)
}

/** Pass a saved answer on. The guest record has no rewards, so nothing is said for it. */
export function announce(saved) {
  if (!saved?.rewards) return
  for (const listen of listeners) listen(saved)
}

/** The name of a level: the highest rank it has reached. */
export const rankOf = (level) => config.ranks.findLast((rank) => level >= rank.from) ?? config.ranks[0]

/** How far through its level, 0 to 1. */
export const shareOf = ({ into, need }) => (need > 0 ? Math.min(1, into / need) : 0)

export const FLOAT_MS = config['float-ms']
