/**
 * XP on the page: the learner's clock, level names, and the earn announcer.
 * The server counts (services/rewards.py); recordAttempt calls `announce`, so every tab earns for free.
 */
import config from '../config/rewards.json'

/** Minutes east of UTC, so "today" is the learner's day. */
export const tz = (now = new Date()) => -now.getTimezoneOffset() || 0

const listeners = new Set()

/** Listen for saved answers with rewards. Returns the unsubscribe. */
export function onEarned(listen) {
  listeners.add(listen)
  return () => listeners.delete(listen)
}

/** Pass a saved answer on; guest answers (no rewards) are skipped. */
export function announce(saved) {
  if (!saved?.rewards) return
  for (const listen of listeners) listen(saved)
}

/** A level's name: the highest rank reached. */
export const rankOf = (level) => config.ranks.findLast((rank) => level >= rank.from) ?? config.ranks[0]

/** Progress through the level, 0 to 1. */
export const shareOf = ({ into, need }) => (need > 0 ? Math.min(1, into / need) : 0)

export const FLOAT_MS = config['float-ms']

/** Daily goal choices (as remembered strings) and the default. */
export const GOALS = config.goals.map(String)
export const GOAL = String(config.goal)
