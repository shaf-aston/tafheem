/**
 * Home's "Next in Grow": one step in Grow picked for this learner, down to the lesson (Fiqh › Purity › Wudu), with why.
 * The worlds are ranked from the record (lib/grow/suggest.js); only the top books' indexes and records are fetched, to
 * find the step, so Home does not load every world. A world with nothing left falls through to the next. One tap
 * starts the step (a handed Grow address). While it is being worked out its place is held (a quiet bar the height of the
 * step, so the page below does not jump when it lands, but only where the last visit showed a step: a first visit has
 * none to hold a place for); nothing when it is where you stopped.
 * `studiedOnly`: only a world the learner has been studying (Home's first screen, where the level picker offers the rest).
 * With an answered first-visit plan the places are recommend()'s instead (lib/learner/recommend.js), so a tab that
 * teaches (Colloquial, Memorise) can be the pick too, with the goal it serves as its why; the plan picks on a first
 * screen as well. `skip`: the place on the card ({ tab, value }), not offered twice.
 */
import { useEffect } from 'react'

import { fill } from '../../lib/shell/homeCopy'
import { bookStep, lessonStep, rankWorlds } from '../../lib/grow/suggest'
import { useBookWorlds } from '../../lib/grow/useBookWorld'
import { WORLDS, worldOf } from '../../lib/grow/worlds'
import { answered, recommend } from '../../lib/learner/recommend'
import { STEPS } from '../../lib/learner/plan'
import { accentOf, LISTED } from '../../lib/nav/tabs'
import { useRememberedFlag } from '../../lib/store/useRemembered'
import { Skeleton } from '../ui/feedback/Skeleton'
import Tile from '../ui/display/Tile'
import ArabicText from '../ui/text/ArabicText'

/** Remembered: whether the last visit offered a step, so this one holds its place. */
export const OFFERED = 'home-grow-next'

// Books looked into at once: the top one, and the next in case it is finished.
const LOOKED = 2

const GOALS = STEPS.find((step) => step.id === 'goals').options

/** recommend()'s places as ranked worlds and tabs: `why` is `recent` (practised lately), `goal` or `level`. */
function fromPlan(plan, modules) {
  return recommend(plan, modules).map(({ place, why }) => ({
    world: place.world && worldOf(place.world),
    tab: place.tab && LISTED.find((tab) => tab.id === place.tab),
    why: why.done ? 'recent' : why.goal ? 'goal' : 'level',
    goal: GOALS.find((option) => option.id === why.goal)?.label,
  })).filter((one) => one.world || one.tab)
}

/** The first ranked world with a step, or undefined while a book it waits on is still loading. */
function pick(ranked, books) {
  for (const one of ranked) {
    if (one.tab) return { ...one, step: { trail: [one.tab.label] } }
    if (one.world.kind !== 'book') return { ...one, step: lessonStep(one.world) }
    const state = books[one.world.id]
    if (!state || (!state.ready && !state.error)) return undefined
    const step = state.ready && bookStep(one.world, state)
    if (step) return { ...one, step }
  }
  return null
}

export default function GrowNext({ modules, pending = false, level, plan, copy, skip, studiedOnly = false, onGo }) {
  const planned = Boolean(plan && answered(plan))
  const ranked = planned
    ? fromPlan(plan, modules)
    : rankWorlds(WORLDS, modules, level).filter((one) => !studiedOnly || one.why === 'recent')
  const books = useBookWorlds(ranked.filter((one) => one.world?.kind === 'book').slice(0, LOOKED).map((one) => one.world), null)
  const found = pick(ranked, books)
  const [expected, expect] = useRememberedFlag(OFFERED, false)
  const settled = !pending && found !== undefined
  const tabId = found && (found.tab ? found.tab.id : 'grow')
  const twice = Boolean(skip) && found && skip.tab === tabId && (tabId !== 'grow' || skip.value === found.step.value)
  const offered = settled && Boolean(found) && !twice
  const label = copy[planned ? 'next-plan-label' : 'next-label']
  useEffect(() => { if (settled) expect(offered) }, [settled, offered, expect])
  if (!settled) {
    if (!expected) return null
    return (
      <section aria-labelledby="home-grow-next" className="space-y-2">
        <h3 id="home-grow-next" className="eyebrow eyebrow-lg">{label}</h3>
        <Skeleton className="h-17 w-full rounded-[var(--radius-lg)]" />
      </section>
    )
  }
  if (!offered) return null
  const { world, tab, why, goal, step } = found
  const accent = tab ? accentOf(tab.id) : world.accent
  const reason = step.due
    ? (step.due === 1 ? copy['next-due-one'] : fill(copy['next-due-many'], { n: step.due }))
    : why === 'goal' ? fill(copy['next-goal'], { goal }) : copy[why === 'recent' ? 'next-recent' : 'next-level']
  return (
    <section aria-labelledby="home-grow-next" className="space-y-2">
      <h3 id="home-grow-next" className="eyebrow eyebrow-lg">{label}</h3>
      {/* A chip, not a second lead block: "where you stopped" stays the one big thing. */}
      <div className="grid">
        <Tile variant="chip" accent={accent} className="py-3" onClick={() => (tab ? onGo(tab.id) : onGo('grow', step.value))}>
          <span className="flex items-center gap-3 min-w-0">
            <ArabicText size="lg" className="min-w-14 shrink-0 text-center" style={{ color: accent }}>{(tab ?? world).arabic}</ArabicText>
            {/* The step itself in bold; the way down to it (book › part) small above; why, under. */}
            <span className="grid min-w-0">
              {step.trail.length > 1 && <span className="type-small text-[var(--text-dim)]">{step.trail.slice(0, -1).join(' › ')}</span>}
              <span className="font-semibold">{step.trail.at(-1)}</span>
              <span className="type-small text-[var(--text-faint)]">{reason}</span>
            </span>
          </span>
          <span aria-hidden="true" className="type-title" style={{ color: accent }}>›</span>
        </Tile>
      </div>
    </section>
  )
}
