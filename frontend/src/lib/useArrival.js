/**
 * A word arriving on a panel that is already open, and what stays on screen
 * while its answer is fetched.
 *
 * A word arrives when it is handed over from another tab, and equally when the
 * back arrow returns to one, and App used to answer that by remounting the
 * whole panel. That tore the column down, faded it in again from nothing over
 * 220ms, and left the page collapsed to an empty panel's height for the length
 * of the request. Together they read as the screen blinking. A back press is a
 * return to a page already read; it must not look like a page being built.
 *
 * So the panel stays and follows the word instead. `useArrival` says when to
 * follow and whether the reader asked for this, and `useHeld` keeps the answer
 * already on screen until the new one lands.
 *
 * A return is not a question. A search the reader typed is, and each panel
 * keeps whatever it already does for one: Daleel replaces its passages with a
 * skeleton rather than leaving stale ones under a spinner, Sarf says nothing
 * for a wait too short to be news. Nothing here changes that.
 */
import { useState } from 'react'

/**
 * Two things about an arrival: `arrived` is true on the one render it comes in,
 * and `returning` stays true until its answer has been fetched. A panel with
 * nothing to hold on screen wants only the first and leaves `pending` out.
 *
 * It takes App's arrival number rather than the word, because the word is not
 * enough: a panel's own searches are steps on the journey too, so the back
 * arrow can land on the very word already in its box, and that is still an
 * arrival to follow.
 *
 * State is adjusted during render, which is the pattern React blesses for
 * following a prop: the corrected render is the first one painted, so the box
 * never shows the previous word for a frame the way an effect would.
 */
export function useArrival(arrival, pending = false) {
  const [seen, setSeen] = useState(arrival)
  const [returning, setReturning] = useState(false)
  const [wasPending, setWasPending] = useState(pending)

  const arrived = arrival !== seen
  if (arrived) {
    setSeen(arrival)
    setReturning(true)
  }
  // Cleared on the falling edge of the request, not merely on "not pending":
  // the arrival is noticed a render before the fetch it starts, so a plain
  // `!pending` would clear it in the gap between the two.
  if (pending !== wasPending) {
    setWasPending(pending)
    if (!pending) setReturning(false)
  }

  return { arrived, returning }
}

/** What to keep showing, given what is held now. Pure, so it can be tested. */
export function nextHeld(held, data, returning) {
  if (data) return data
  return returning ? held : null
}

/**
 * The answer to keep on screen through a return. It goes the moment the request
 * stops without one, which is what keeps a failure honest: an error alert over
 * the previous word's answer would be a lie about what failed.
 */
export function useHeld(data, returning) {
  const [held, setHeld] = useState(null)
  const shown = nextHeld(held, data, returning)
  if (shown !== held) setHeld(shown)
  return shown
}
