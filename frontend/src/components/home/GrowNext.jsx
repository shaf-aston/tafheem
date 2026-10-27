/**
 * Home's "Next in Grow": one step in Grow picked for this learner, down to the lesson (Fiqh › Purity › Wudu), with why.
 * The worlds are ranked from the record (lib/grow/suggest.js); only the top books' indexes and records are fetched, to
 * find the step, so Home does not load every world. A world with nothing left falls through to the next. One tap
 * starts the step (a handed Grow address). While it is being worked out its place is held (a quiet bar the height of the
 * step, so the page below does not jump when it lands); nothing when it is where you stopped.
 * `studiedOnly`: only a world the learner has been studying (Home's first screen, where the level picker offers the rest).
 */
import { fill } from '../../lib/shell/homeCopy'
import { bookStep, lessonStep, rankWorlds } from '../../lib/grow/suggest'
import { useBookWorlds } from '../../lib/grow/useBookWorld'
import { WORLDS } from '../../lib/grow/worlds'
import { Skeleton } from '../ui/feedback/Skeleton'
import Tile from '../ui/display/Tile'
import ArabicText from '../ui/text/ArabicText'

// Books looked into at once: the top one, and the next in case it is finished.
const LOOKED = 2

/** The first ranked world with a step, or undefined while a book it waits on is still loading. */
function pick(ranked, books) {
  for (const one of ranked) {
    if (one.world.kind !== 'book') return { ...one, step: lessonStep(one.world) }
    const state = books[one.world.id]
    if (!state || (!state.ready && !state.error)) return undefined
    const step = state.ready && bookStep(one.world, state)
    if (step) return { ...one, step }
  }
  return null
}

export default function GrowNext({ modules, pending = false, level, copy, skip, studiedOnly = false, onGo }) {
  const ranked = rankWorlds(WORLDS, modules, level).filter((one) => !studiedOnly || one.why === 'recent')
  const books = useBookWorlds(ranked.filter((one) => one.world.kind === 'book').slice(0, LOOKED).map((one) => one.world), null)
  const found = pick(ranked, books)
  if (pending || found === undefined) {
    return (
      <section aria-labelledby="home-grow-next" className="space-y-2">
        <h3 id="home-grow-next" className="eyebrow eyebrow-lg">{copy['next-label']}</h3>
        <Skeleton late className="h-17 w-full rounded-[var(--radius-lg)]" />
      </section>
    )
  }
  if (!found || found.step.value === skip) return null
  const { world, why, step } = found
  const { accent } = world
  const reason = step.due
    ? (step.due === 1 ? copy['next-due-one'] : fill(copy['next-due-many'], { n: step.due }))
    : copy[why === 'recent' ? 'next-recent' : 'next-level']
  return (
    <section aria-labelledby="home-grow-next" className="space-y-2">
      <h3 id="home-grow-next" className="eyebrow eyebrow-lg">{copy['next-label']}</h3>
      {/* A chip, not a second lead block: "where you stopped" stays the one big thing. */}
      <div className="grid">
        <Tile variant="chip" accent={accent} className="py-3" onClick={() => onGo('grow', step.value)}>
          <span className="flex items-center gap-3 min-w-0">
            <ArabicText size="lg" className="min-w-14 shrink-0 text-center" style={{ color: accent }}>{world.arabic}</ArabicText>
            {/* The step itself in bold; the way down to it (book › part) small above; why, under. */}
            <span className="grid min-w-0">
              {step.trail.length > 1 && <span className="type-small text-[var(--text-dim)]">{step.trail.slice(0, -1).join(' › ')}</span>}
              <span className="font-semibold">{step.trail.at(-1)}</span>
              <span className="type-small text-[var(--text-faint)]">{reason}</span>
            </span>
          </span>
          <span aria-hidden="true" className="text-xl" style={{ color: accent }}>›</span>
        </Tile>
      </div>
    </section>
  )
}
