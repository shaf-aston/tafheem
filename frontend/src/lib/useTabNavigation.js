import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'

import { DOCK, FIXED, LISTED, RECENT, TABS } from './tabs'
import { useDock } from './dock'
import { keepRecent, useStrip } from './recent'
import { lastPlaceOn, onJump, startJourney, visit } from './journey'
import { holdBackdrop } from './backdropHold'
import { useTabShortcuts } from './useTabShortcuts'
import { scrollToTop } from './scrollToEl'

// Nothing to say about a round: no streak, no answer just given.
export const QUIET = { streak: 0, answer: null }

// Numbers the arrivals. A panel cannot tell "this word has come again" from
// "this word never left" by the word alone: its own searches are steps on the
// journey too, so the back arrow can land on the word already in its box. The
// number is what says an arrival happened. It must never repeat, which a clock
// can: two arrivals can share a millisecond.
let arrivals = 0

// Tabs kept alive while hidden, the most recently opened: going back to one
// shows it as it was left, what was typed, read and scrolled. Each costs its
// page's memory, nothing while hidden; more would be paying for tabs that are
// not coming back.
const KEEP = 4

// How long the backdrop holds still for a switch (lib/backdropHold).
const SWITCH_MS = 400

/**
 * Every way between tabs, in one place: which tab is on screen, which are kept
 * alive behind it, the word each was handed, the browser's back arrow, the
 * number keys, and the two bars (the strip's recent tabs, the phone's dock).
 * `switchTab(id, word?)` is the one way onto a tab; `said[id]` is how a panel
 * reports where it got to and how a practice round is going, heard only from
 * the tab on screen; `round` is the latest such report, for the pen.
 */
export function useTabNavigation() {
  // Where the journey lands: the address if it names a word, else the tab's
  // last word from the saved path. Started here, before the first render, so
  // the panel is born on that word rather than remounted onto it.
  const [opened] = useState(() => startJourney(TABS) ?? { tab: TABS[0].id, value: null })
  const [activeTab, setActiveTab] = useState(opened.tab)
  const [alive, setAlive] = useState([opened.tab])
  // The same two, for the callbacks below to read without being remade.
  const activeRef = useRef(opened.tab)
  const aliveRef = useRef(alive)
  // A root handed from one tab to another, per tab. Held here because it is the
  // only thing the panels share; each one reads it once and then owns its own state.
  const [handoffs, setHandoffs] = useState(
    opened.value ? { [opened.tab]: { value: opened.value, at: 0 } } : {},
  )
  // The practice tabs (Quiz, Tamreen) say how it is going.
  // They report; `moodFrom` in the header is still the only thing that decides.
  const [round, setRound] = useState(QUIET)
  // How far down each tab was left. The page is one scroll for every tab, so
  // without this a tab opened from halfway down another opens halfway down too.
  // Coming back finds the tab where it was; a tab new to the visit, or handed
  // a new word, opens at the top.
  const scrolled = useRef({})

  // Every way onto a tab. `arrive`: the word it brings is one for the panel to
  // follow; without, a tab still alive is shown exactly as it was left.
  const show = useCallback((id, value, arrive) => {
    holdBackdrop(SWITCH_MS)
    if (id !== activeRef.current) scrolled.current[activeRef.current] = globalThis.scrollY ?? 0
    if (arrive) delete scrolled.current[id]
    activeRef.current = id
    setActiveTab(id)
    // Leaving the quiz ends the round as far as the pen is concerned, a streak
    // face still on while reading the Qur'an is describing nothing.
    setRound(QUIET)
    const kept = aliveRef.current.includes(id)
    aliveRef.current = keepRecent(aliveRef.current, id, KEEP)
    setAlive(aliveRef.current)
    if (!arrive && kept) return
    const handoff = value ? { value, at: ++arrivals } : null
    setHandoffs((all) => ({ ...all, [id]: handoff }))
  }, [])

  // A tab chosen with nothing in hand opens on the word it was last on, from
  // the journey, so glancing at another tab and coming back costs nothing; one
  // still alive is simply shown again. Already there (the active tab clicked
  // again): not a step, and the panel is left exactly as it is.
  const switchTab = useCallback((id, handed = null) => {
    const value = handed ?? lastPlaceOn(id)
    if (!visit(id, value)) return
    show(id, value, handed != null)
  }, [show])

  // Before paint, so the old tab's place never flashes on the new one. Skips
  // the first render: a reload keeps the browser's own restored place.
  const first = useRef(true)
  useLayoutEffect(() => {
    if (first.current) { first.current = false; return }
    const top = scrolled.current[activeTab]
    if (top) globalThis.scrollTo?.({ top, behavior: 'instant' })
    else scrollToTop()
  }, [activeTab])

  const strip = useStrip(LISTED, FIXED, RECENT, activeTab)
  const [dock, placeInDock] = useDock(LISTED, DOCK)

  useTabShortcuts(strip, switchTab)

  // The trail and the browser's back arrow are the same list; this follows the
  // arrow: a step returned to is handed back to its panel exactly like a
  // hand-off, which is what makes it load that word again.
  useEffect(() => {
    return onJump((step) => show(step.tab, step.value, step.value != null))
  }, [show])

  // Each panel's own way to report where it got to, and how a round is going:
  // made once, so a hidden panel is not rendered again for a switch. Only the
  // tab on screen is heard; a hidden one finishing a search is not a step.
  const said = useMemo(() => Object.fromEntries(TABS.map(({ id }) => [id, {
    onVisit: (value) => activeRef.current === id && visit(id, value),
    onProgress: (report) => { if (activeRef.current === id) setRound(report) },
  }])), [])

  return { activeTab, alive, handoffs, switchTab, said, round, strip, dock, placeInDock }
}
