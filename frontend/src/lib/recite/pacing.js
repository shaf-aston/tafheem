/** When to cut a recording and when to ask for a reading: pure timing rules, no I/O. */
import config from '../../config/recite.json'

/**
 * Why a recording should stop itself: a pause after a phrase, or long enough
 * is long enough. Null before any voice has been heard in this window at
 * all, on purpose: a reciter thinking before starting is never cut, that is
 * left to the microphone's own quiet-stop.
 */
export const cutReason = (now, began, lastVoice, pauseMs, windowMs) => {
  if (lastVoice < began) return null
  if (now - lastVoice >= pauseMs) return 'pause'
  if (now - began >= windowMs) return 'max'
  return null
}

/** Whether a voice has been heard since this recording began, allowing for the meter's own lag. */
export const spokeSince = (lastVoice, began, lagMs) => lastVoice >= began - lagMs

/**
 * The asks of the last minute, newest last, with the older ones dropped. What
 * the ear's allowance is counted against; see allowanceLeft.
 */
export const recentAsks = (now, asks) => asks.filter((at) => now - at < 60000)

/**
 * How many more readings may be asked for right now. Both kinds are counted,
 * the mid-phrase ones and the one at each pause, because the ear's allowance
 * does not tell them apart. Only the mid-phrase ones give way to it.
 */
export const allowanceLeft = (now, asks, perMinute) => perMinute - recentAsks(now, asks).length

/**
 * How many readings a minute to ask for: the server's own count (its listening
 * keys times each key's allowance) less the margin recite.json explains, or the
 * fixed figure when the server gave none.
 */
export const asksPerMinute = (fromServer) =>
  fromServer > 0 ? Math.floor(fromServer * config['asks-share']) : config['asks-per-minute']

/** Whether it is time to ask for a reading: free, something new to send, paced by how long the last one took, and inside the ear's allowance. */
export const readyToSend = (now, asked, took, stepMs, busy, chunksLen, sent, left = Infinity) =>
  !busy && chunksLen > sent && now - asked >= Math.max(stepMs, took) && left > 0
