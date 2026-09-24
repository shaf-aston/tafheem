/**
 * The smaller events inside one opened event, as a numbered run down the page.
 *
 * Open on arrival, always. Reading is what this is for, and a reader who has to
 * click six times to see six steps has been charged for the thing he came to
 * do. Folding is for skimming a long event, so only a step worth skipping can
 * fold (lib/timelineLayout canFold: it holds moments, runs long, or is marked
 * aside), an aside arrives folded, and one "Fold all" button at the top folds them all.
 *
 * "Walk through" reads the run one step at a time: the step being read is lit,
 * the arrow keys turn to the next or back, and the map and the where-am-I line
 * follow it (the section owns which step that is, as `here`). Steps that name a
 * path (the believer, the disbeliever) are read side by side as lanes.
 *
 * A moment inside a step is drawn by this same component one rung in: the data
 * is recursive (services/timelines caps it at STEP_DEPTH), so the drawing is.
 */
import { useEffect, useRef, useState } from 'react'

import ArabicText from './ui/ArabicText'
import SmallButton from './ui/SmallButton'
import TimelineHadith from './TimelineHadith'
import TimelineRefs from './TimelineRefs'
import { TRAD, canFold, pathRows, readingOrder, stepIds } from '../lib/timelineLayout'
import { scrollToEl } from '../lib/scrollToEl'

/** The fold arrow on both fold controls: down when open, turned right when shut. */
function FoldMark({ shut }) {
  return (
    <span
      className="inline-block transition-transform"
      style={{ transform: shut ? 'rotate(-90deg)' : 'none' }}
      aria-hidden="true"
    >
      ▾
    </span>
  )
}

/** One rung of the run, drawn the same at every depth but quieter as it goes in. */
function Step({ step, n, depth, ctx }) {
  const { library, accent, onGo, shut, toggle, here, pick, glideRef, prints } = ctx
  const kids = step.steps ?? []
  const isShut = shut.has(step.id)
  const isHere = here === step.id
  // Said beside the place, as on the event, never as a pill of its own.
  const traditional = step.flags?.includes(TRAD)
  const place = step.place
    ? `${library.places[step.place]?.name}${traditional ? `, ${library.flags[TRAD]}` : ''}`
    : null
  const ref = useRef(null)

  // A step turned to by the walk is brought to the middle of the screen; one
  // pressed by hand is already where the reader is looking, so it stays put.
  useEffect(() => {
    if (!isHere || glideRef.current !== step.id) return
    glideRef.current = null
    scrollToEl(ref.current, 'center')
  }, [isHere, glideRef, step.id])

  return (
    <li ref={ref} className="relative ps-7">
      {/* The number sits on the line, so the run reads as one thread rather
          than as a list that happens to be numbered. */}
      <span
        className="absolute start-0 top-0.5 grid place-items-center w-5 h-5 rounded-full
          type-tiny font-semibold border transition-colors"
        style={{
          borderColor: accent,
          color: isHere ? 'var(--bg)' : accent,
          background: isHere ? accent : 'var(--surface)',
        }}
        aria-hidden="true"
      >
        {n}
      </span>

      <div className="flex items-baseline gap-2 flex-wrap">
        {/* Pressing a title makes it the step being read: the map and the
            where-am-I line move to it. */}
        <button
          type="button"
          onClick={() => pick(step.id)}
          aria-current={isHere ? 'step' : undefined}
          className={`${depth ? 'text-sm' : 'text-sm font-medium'} text-start text-[var(--text)]
            underline-offset-4 decoration-dotted hover:underline`}
          style={isHere ? { color: accent } : undefined}
        >
          {step.title}
        </button>
        {step.arabic && (
          <ArabicText size="tiny" className="arabic-inline text-[var(--text-faint)]">{step.arabic}</ArabicText>
        )}
        {(step.when || place) && (
          <span className="type-tiny text-[var(--text-faint)]">
            {[step.when, place].filter(Boolean).join(' · ')}
          </span>
        )}
      </div>

      {/* Folded, a step is its title and the button: the story, its sources
          and its moments all wait behind it. */}
      {!isShut && (
        <>
          <p className="text-sm text-[var(--text-dim)] leading-snug max-w-prose mt-0.5">{step.summary}</p>

          <TimelineRefs
            flags={step.flags?.filter((f) => f !== TRAD)}
            refs={step.refs}
            library={library}
            accent={accent}
            onGo={onGo}
            className="pt-1.5"
          />

          <TimelineHadith refs={step.refs} only={prints?.get(step.id)} library={library} accent={accent} className="pt-2" />
        </>
      )}

      {canFold(step) && (
        <button
          type="button"
          onClick={() => toggle(step.id)}
          aria-expanded={!isShut}
          className="mt-1 inline-flex items-center gap-1.5 type-tiny rounded-full border px-2 py-0.5
            transition-colors hover:bg-[var(--surface-hi)]"
          style={{ color: accent, borderColor: `color-mix(in srgb, ${accent} 35%, var(--border))` }}
        >
          <FoldMark shut={isShut} />
          {foldLabel(step, isShut)}
        </button>
      )}

      {!isShut && kids.length > 0 && <Run steps={kids} depth={depth + 1} ctx={ctx} />}
    </li>
  )
}

/**
 * One run of steps, with the thread they hang from drawn behind the numbers.
 * Neighbouring steps on different paths share a row, one lane each, and share
 * their numbers too: they happen at the same time.
 */
function Run({ steps, depth, ctx }) {
  return (
    <ol
      className="relative list-none m-0 mt-2 p-0 space-y-3 border-s"
      style={{ borderColor: `color-mix(in srgb, ${ctx.accent} 35%, transparent)`, marginInlineStart: '0.625rem' }}
    >
      {pathRows(steps).map((row) => (row.step
        ? <Step key={row.step.id} step={row.step} n={row.n} depth={depth} ctx={ctx} />
        : (
          <li key={row.lanes[0].steps[0].id} className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
            {row.lanes.map((lane, l) => (
              <section key={lane.path} aria-label={ctx.library.paths?.[lane.path] ?? lane.path} className="min-w-0">
                <p className="ps-7 type-tiny uppercase tracking-wide text-[var(--text-faint)] m-0" aria-hidden="true">
                  {ctx.library.paths?.[lane.path] ?? lane.path}
                </p>
                {/* Lanes after the first hang from a thread of their own. */}
                <ol
                  className={`list-none m-0 mt-1 p-0 space-y-3 ${l ? 'border-s' : ''}`}
                  style={l ? { borderColor: `color-mix(in srgb, ${ctx.accent} 35%, transparent)` } : undefined}
                >
                  {lane.steps.map((step, i) => (
                    <Step key={step.id} step={step} n={row.n + i} depth={depth} ctx={ctx} />
                  ))}
                </ol>
              </section>
            ))}
          </li>
        )))}
    </ol>
  )
}

/** What the fold button says: what is behind it, or that it shuts. */
function foldLabel(step, isShut) {
  const kids = (step.steps ?? []).length
  if (kids) return `${kids} ${kids === 1 ? 'moment' : 'moments'} inside`
  if (step.aside) return isShut ? 'Side detail, read it' : 'Side detail, fold it'
  return isShut ? 'Read the rest' : 'Fold'
}

/** A key press that belongs to a text box, not to the walk. */
const typing = (target) => Boolean(target.closest?.('input, textarea, select, [contenteditable="true"]'))

export default function TimelineSteps({ steps, prints, library, accent, onGo, here, onHere, at }) {
  // Side details start folded; everything else starts open.
  const [shut, setShut] = useState(() => new Set(stepIds(steps, (s) => s.aside)))
  const foldable = stepIds(steps, canFold)
  const allShut = foldable.length > 0 && foldable.every((id) => shut.has(id))
  const order = readingOrder(steps)
  const pos = order.findIndex((r) => r.step.id === here)
  const walking = pos >= 0
  const glideRef = useRef(null)
  const sectionRef = useRef(null)
  const barRef = useRef(null)
  const wasWalking = useRef(walking)

  const toggle = (id) => setShut((was) => {
    const next = new Set(was)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    return next
  })

  // Walking onto a step opens it and everything it sits inside, so the step
  // being read is never behind a fold.
  const walk = (i, scroll = true) => {
    const r = order[i]
    if (!r) return
    glideRef.current = scroll ? r.step.id : null
    setShut((was) => {
      const next = new Set(was)
      for (const s of [r.step, ...r.above]) next.delete(s.id)
      return next
    })
    onHere(r.step.id)
  }
  const pick = (id) => walk(order.findIndex((r) => r.step.id === id), false)

  // Arrow keys turn the page while a walk is on; Escape ends it. Only when
  // nothing else holds the keyboard: the page itself, or somewhere in this run.
  useEffect(() => {
    if (!walking) return undefined
    const onKey = (e) => {
      const ours = e.target === document.body || sectionRef.current?.contains(e.target)
      if (!ours || typing(e.target) || e.altKey || e.ctrlKey || e.metaKey) return
      if (e.key === 'ArrowRight') walk(pos + 1)
      else if (e.key === 'ArrowLeft') walk(pos - 1)
      else if (e.key === 'Escape') onHere(null)
      else return
      e.preventDefault()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  // Starting or stopping swaps the buttons under the reader's keyboard; the
  // focus goes to the control that replaced the one pressed, not to the page.
  useEffect(() => {
    if (wasWalking.current === walking) return
    wasWalking.current = walking
    if (document.activeElement === document.body || !document.activeElement) {
      barRef.current?.querySelector(walking ? '[data-walk="next"]' : '[data-walk="start"]')?.focus()
    }
  }, [walking])

  const ctx = { library, accent, onGo, shut, toggle, here, pick, glideRef, prints }

  return (
    <section ref={sectionRef} className="pt-3 mt-3 border-t border-[var(--border)]">
      {/* While walking, this bar stays pinned under the app header, carrying
          the step and its place, since the map above scrolls away. */}
      <div
        ref={barRef}
        className={`flex items-center gap-2 flex-wrap ${walking ? `sticky z-10 top-[calc(var(--app-header-h,0px)+0.5rem)]
          -mx-2 px-2 py-1.5 rounded-[var(--radius-sm)] bg-[var(--surface)] border border-[var(--border)]` : ''}`}
      >
        {!walking
          ? (
            <h4 className="type-tiny uppercase tracking-wide text-[var(--text-faint)] m-0">
              Inside this event · {order.length} {order.length === 1 ? 'step' : 'steps'}
            </h4>
          )
          : (
            <p className="type-small m-0 min-w-0 truncate" aria-live="polite">
              <span style={{ color: accent }}>{order[pos].step.title}</span>
              {at && <span className="text-[var(--text-faint)]"> · {library.places[at]?.name}</span>}
              <span className="sr-only">, step {pos + 1} of {order.length}</span>
            </p>
          )}
        <div className="ms-auto flex items-center gap-1.5">
          {!walking
            ? <SmallButton data-walk="start" onClick={() => walk(0)} style={{ color: accent }}>▸ Walk through</SmallButton>
            : (
              <>
                <SmallButton onClick={() => walk(pos - 1)} disabled={pos === 0} aria-label="Previous step">‹</SmallButton>
                <span className="type-small tabular-nums text-[var(--text-dim)]" aria-hidden="true">
                  {pos + 1} of {order.length}
                </span>
                <SmallButton
                  data-walk="next"
                  onClick={() => walk(pos + 1)}
                  disabled={pos === order.length - 1}
                  aria-label="Next step"
                >
                  ›
                </SmallButton>
                <SmallButton onClick={() => onHere(null)} title="Stop (Esc)">Stop</SmallButton>
              </>
            )}
          {foldable.length > 0 && (
            <SmallButton
              onClick={() => setShut(allShut ? new Set() : new Set(foldable))}
              aria-expanded={!allShut}
              className="inline-flex items-center gap-1.5 text-[var(--text-dim)] hover:text-[var(--text)]"
            >
              <FoldMark shut={allShut} />
              {/* Worded, not a bare arrow: a square with a triangle said nothing. */}
              {allShut ? 'Open all' : 'Fold all'}
            </SmallButton>
          )}
        </div>
      </div>

      <Run steps={steps} depth={0} ctx={ctx} />
    </section>
  )
}
