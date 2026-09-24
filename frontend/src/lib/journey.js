/**
 * Where the reader has been, and the back arrow that agrees with it.
 *
 * One store feeds two things that must never disagree: the trail line under the
 * header, and the browser's own back arrow. Both are this list of steps; the
 * arrow moves the index, the trail draws it.
 *
 * A step is a place actually reached (a search that came back), never a
 * keystroke, so the trail is a path rather than a log. The index rides in
 * history.state, which is what lets a back press say WHICH step it landed on;
 * popstate on its own only says that something moved.
 *
 * The list is saved on every change (lib/session.js) and read back at start,
 * so a reload keeps the path. The browser keeps history.state across a reload
 * too, which is how `resume` knows which saved step the address is.
 *
 * Mirrors settings.js: module state, listeners, useSyncExternalStore.
 */
import { useSyncExternalStore } from 'react'

import { forgetProgress } from './progress'
import { forgetTamreenAnswers } from './tamreenAnswers'
import { forgetSession, loadSession, samePlace, saveSession } from './session'
import { readRouteFromUrl, readStateFromHistory, writeTabToUrl } from './tabUrl'

const listeners = new Set()
const jumpListeners = new Set()

// Every place visited this session, oldest first, and where the browser sits.
let snapshot = { steps: [], at: -1 }
let tabIds = []

// The one write point: every change to the path is saved here, including a
// back press, so a reload after going back lands on the step gone back to.
// A path with no word on it yet is not saved: merely opening the app should
// leave nothing behind, and "clear saved data" then reload must show nothing.
function set(next) {
  snapshot = { ...snapshot, ...next }
  if (snapshot.steps.some((step) => step.value)) saveSession(snapshot, tabIds)
  for (const listener of listeners) listener()
}

/** The path with `place` reached from step `at`: it goes next, and what was ahead is dropped. */
function stepOnto(steps, at, place) {
  const walked = [...steps.slice(0, at + 1), place]
  return { steps: walked, at: walked.length - 1 }
}

/**
 * Where a fresh page load sits on a saved path.
 *
 * The address is the truth for where we ARE; the saved steps are the truth for
 * where we have BEEN. Three cases, in order:
 *   1. the step the browser's own history names is this address: a reload, or
 *      a back press that crossed a reload. Sit there, keep everything.
 *   2. the saved current step is this address (no usable history.state). Same.
 *   3. neither: a pasted or typed link. It is a new place, so it goes after the
 *      current step like any visit.
 * A bare address (a tab, no word) means "the app", not "a blank": it opens on
 * the tab's last word, the way a bookmark should. No saved path: the address
 * is step zero.
 */
export function resume(saved, asked, stateStep) {
  if (!saved) return { steps: [asked], at: 0 }
  const { steps, at } = saved
  const here = asked.value ? asked : { tab: asked.tab, value: lastOn(steps, at, asked.tab) }
  if (Number.isInteger(stateStep) && samePlace(steps[stateStep], here)) return { steps, at: stateStep }
  if (samePlace(steps[at], here)) return { steps, at }
  return stepOnto(steps, at, here)
}

/**
 * Read the address bar and the saved path, sit on the right step, then follow
 * the back arrow. Returns the place sat on, so App can open its panel there.
 */
export function startJourney(tabs) {
  if (!globalThis.window) return null
  if (tabIds.length) return placeNow()
  tabIds = tabs.map((tab) => tab.id)
  land(loadSession(tabIds), tabs)

  window.addEventListener('popstate', (event) => {
    const step = event.state?.step
    // The entry is one of ours only if its step is this address. An index
    // alone is not enough: history from before the path expired carries step
    // numbers of a path that is gone, and one of them can point at a step of
    // this path that is a different word.
    if (!samePlace(snapshot.steps[step], readRouteFromUrl(tabs))) {
      // The address is still the truth, so it is walked onto from here rather
      // than ignored, which would leave the panel behind the address.
      land(snapshot, tabs)
    } else {
      set({ at: step })
    }
    for (const listener of jumpListeners) listener(snapshot.steps[snapshot.at])
  })
  return placeNow()
}

/** The step the reader is on. */
export const placeNow = () => snapshot.steps[snapshot.at] ?? null

// Sit on the step the address names, and stamp that step onto the history entry.
// An address naming no tab is the app itself: it opens where the reader last
// was, or on the first tab when there is no last.
function land(saved, tabs) {
  const asked = readRouteFromUrl(tabs)
  const wanted = asked.tab ? asked : (saved?.steps[saved.at] ?? { tab: tabs[0].id, value: null })
  const landed = resume(saved, wanted, readStateFromHistory().step)
  const here = landed.steps[landed.at]
  writeTabToUrl(here.tab, here.value, { replace: true, state: { step: landed.at } })
  set(landed)
}

/**
 * Called when the browser itself moves us, back or forward, and never on a new
 * search: a search is already on screen, a step returned to has to be loaded
 * again. App listens and hands the step's word back to the panel.
 */
export function onJump(listener) {
  jumpListeners.add(listener)
  return () => jumpListeners.delete(listener)
}

/**
 * Record a place reached. True if it was a step; false for a repeat of where
 * we already are, which is not one, and nothing on screen should move for it.
 */
export function visit(tab, value = null) {
  if (samePlace(snapshot.steps[snapshot.at], { tab, value })) return false
  const next = stepOnto(snapshot.steps, snapshot.at, { tab, value })
  writeTabToUrl(tab, value, { state: { step: next.at } })
  set(next)
  return true
}

/**
 * Start over: forget the path and every saved answer, and reopen the tab
 * we are on with nothing in hand. A load rather than a state change because
 * every panel holds its own word in React state, and the address is the only
 * thing that resets them all. Reopening the same tab, not the first: pressed
 * on the quiz it read as "reset the quiz", and landing on Nahw looked like a
 * wrong turn. Settings and remembered choices stay; that wipe lives in Settings.
 */
export async function startOver() {
  const tab = tabNow(snapshot.steps, snapshot.at) ?? tabIds[0]
  forgetSession()
  forgetTamreenAnswers()
  await forgetProgress()
  globalThis.location?.assign(`${globalThis.location.pathname}?tab=${tab}`)
}

/** Back one step, through the browser so its own arrow stays in step. */
export const goBack = () => globalThis.history?.back()

/** Back to a step already walked, by its index in `steps`. */
export const jumpTo = (step) => globalThis.history?.go(step - snapshot.at)

/**
 * The last place reached on a tab, at or before where we are, or null.
 *
 * What a tab opens on when chosen from the strip with nothing in hand: the
 * word it was on, not a blank. Steps ahead are not counted, they were left by
 * going back.
 */
export function lastOn(steps, at, tab) {
  for (let index = at; index >= 0; index -= 1) {
    if (steps[index].tab === tab && steps[index].value) return steps[index].value
  }
  return null
}

/** `lastOn` for the path as it is now. */
export const lastPlaceOn = (tab) => lastOn(snapshot.steps, snapshot.at, tab)

/**
 * The whole path on one tab, both sides of where we are.
 *
 * Steps ahead are kept, not cut: going back used to erase them from the line,
 * which read as "gone" when they are one click forward. The index each carries
 * is what says which side of `at` it is on, and what a click jumps to.
 *
 * Steps on other tabs are left out. This line sits beside one tab's heading,
 * and a Qur'an address inside a dictionary trail reads as a search that failed.
 *
 * A return to the same word (another tab glanced at, then this one reopened on
 * its last word) is drawn once, not "فهم › فهم": the later step stands in for
 * the earlier, unless the earlier is where we are.
 */
export function trailFor(steps, tab, at = -1) {
  const walked = []
  for (const [index, step] of steps.entries()) {
    if (step.tab !== tab || !step.value) continue
    const last = walked[walked.length - 1]
    if (last && last.value === step.value && last.index !== at) walked.pop()
    if (!(last && last.value === step.value && last.index === at)) walked.push({ ...step, index })
  }
  return walked
}

/** Which tab the reader is on, as the journey has it. */
export const tabNow = (steps, at) => steps[at]?.tab ?? null

/**
 * The few steps around where we are, since the line sits beside a title.
 *
 * A long session is twenty words, and all twenty beside the heading is a
 * paragraph. The ones dropped are the oldest, and they are still in the
 * browser's own history; `sliced` says so, and the line prints an ellipsis.
 */
export function nearest(walked, at, count) {
  if (walked.length <= count) return { shown: walked, sliced: false }
  const here = walked.reduce((n, step, index) => (step.index <= at ? index : n), 0)
  // One step of what is ahead stays in view, the rest of the room goes behind.
  const from = Math.max(0, Math.min(here - count + 2, walked.length - count))
  return { shown: walked.slice(from, from + count), sliced: from > 0 }
}

export function useJourney() {
  return useSyncExternalStore(
    (notify) => {
      listeners.add(notify)
      return () => listeners.delete(notify)
    },
    () => snapshot,
    () => snapshot,
  )
}
