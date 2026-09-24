/**
 * A thing that opens and shuts. The only one in the app.
 *
 * There were four of these written out by hand, and they had drifted: two used
 * the browser's own little triangle, one drew its own, one was in a box and the
 * others were not, and all four picked their own text size. Restyling "the drop
 * downs" meant finding four files and hoping. Now it means this one.
 *
 * Still a real <details> underneath, so opening and shutting is the browser's
 * own behaviour: it works from the keyboard, a screen reader announces it, and
 * it costs no JavaScript. Only the look is ours.
 *
 * Two shapes, because the app genuinely has two: `quiet`, a faint line of text
 * with the content under it, and `framed`, a bordered box with its own header
 * strip for when the content inside is a slab, a wide table say, that needs an
 * edge drawn round it.
 */
import { forwardRef, useState } from 'react'

const TONE = {
  quiet: 'type-small text-[var(--text-faint)] hover:text-[var(--text)]',
  strong: 'text-sm font-medium text-[var(--text)] hover:text-[var(--text)]',
}

const Disclosure = forwardRef(function Disclosure(
  { label, defaultOpen = false, framed = false, tone = 'quiet', onToggle, bodyClassName, className = '', children },
  ref,
) {
  // Framed clips to its rounded corners with overflow-clip, not -hidden:
  // hidden makes the box a scroll container and nothing inside can stay pinned.
  const [open, setOpen] = useState(defaultOpen)
  return (
    <details
      ref={ref}
      open={defaultOpen}
      // Told the truth on every open and shut, so a panel that only fetches
      // once it is open hears about it. React's onToggle fires on the element
      // itself, which is why the flag is read off the target rather than kept.
      // Also drives the glide below: <details> has no CSS hook of its own for
      // "open", so the state is mirrored here.
      onToggle={(event) => {
        setOpen(event.currentTarget.open)
        onToggle?.(event.currentTarget.open)
      }}
      className={`group ${framed ? 'rounded-[var(--radius-md)] border border-[var(--border)] overflow-clip' : ''} ${className}`}
    >
      <summary
        // list-none kills the browser's triangle in every engine, ours is drawn
        // below so that it can rotate and take the accent colour with it.
        className={`list-none cursor-pointer select-none flex items-center gap-2 transition-colors
          ${TONE[tone] ?? TONE.quiet}
          ${framed ? 'px-4 py-2.5 bg-[var(--surface)] text-[var(--text-dim)]' : ''}`}
      >
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          width="11"
          height="11"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          // The timing comes from theme.json like every other movement here.
          // It is stored as a bare number so it can be arithmetic, hence the
          // calc rather than reading the variable straight into a duration.
          style={{ transitionDuration: 'calc(var(--motion-base-ms) * 1ms)' }}
          // A framed bar can carry a figure the height of three of these, and an
          // 11px arrow beside one reads as a speck rather than a control.
          className={`shrink-0 transition-transform group-open:rotate-90 ${framed ? 'w-3.5 h-3.5' : ''}`}
        >
          <path d="M9 5l7 7-7 7" />
        </svg>
        {/* flex-1 so a label that is more than words, the quiz panel hands in a
            row of figures, can spread across the bar and push its own hint to
            the far end. A plain text label is unaffected. */}
        <span className="min-w-0 flex-1">{label}</span>
      </summary>

      <div className="glide" data-open={open}>
        <div className={bodyClassName ?? (framed ? '' : 'mt-2')}>{children}</div>
      </div>
    </details>
  )
})

export default Disclosure
