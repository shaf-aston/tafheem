/**
 * Long text, shown cut to a few lines with the rest one press away.
 *
 * The app used to shut long passages behind a drop-down: nothing on screen but
 * a label, and a reader looking up one root had to open five of them in a row
 * before a single word of a dictionary appeared. A snippet answers the question
 * the label was asking for them, "is this the entry I want", without the press.
 *
 * The cut is measured, not guessed at from a character count: an entry is cut
 * only when it actually overflows the lines given, so a three-line gloss never
 * grows a button that reveals nothing. Measuring again on resize matters here
 * because the same text is four lines wide on a desktop and eleven on a phone.
 *
 * The cut is a height, not line-clamp. Line-clamp only counts lines inside one
 * box, and half of what goes in here is a shape, Lane's entry with a heading
 * per verb form and its senses stepped in under it, where it clamps to nothing
 * or to everything. A height in lines holds either kind, and the fade at the
 * bottom edge says "there is more" before the button is read.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

export default function ShowRest({
  lines = 4,
  // A CSS length wins over the line count, for the one cut that is a tuned
  // knob in theme.json rather than a number picked at the call site.
  height,
  accent,
  more = 'Show all',
  less = 'Show less',
  onOpen,
  // Held by the caller when something else must open the fold, Lane's word
  // index jumping to a section below the cut.
  open: held,
  onOpenChange,
  className = '',
  children,
}) {
  const body = useRef(null)
  const [own, setOwn] = useState(false)
  const open = held ?? own
  const setOpen = onOpenChange ?? setOwn
  const [cut, setCut] = useState(false)

  const measure = useCallback(() => {
    const node = body.current
    if (!node) return
    // Only meaningful while clamped; once open the box is its full height and
    // scrollHeight equals clientHeight, which would read as "nothing hidden".
    if (!open) setCut(node.scrollHeight > node.clientHeight + 1)
  }, [open])

  useEffect(() => {
    measure()
    if (!globalThis.ResizeObserver) {
      globalThis.addEventListener('resize', measure)
      return () => globalThis.removeEventListener('resize', measure)
    }
    const observer = new ResizeObserver(measure)
    observer.observe(body.current)
    return () => observer.disconnect()
  }, [measure, children])

  const reveal = () => {
    const next = !open
    setOpen(next)
    // Told on the way open only. A panel that pays for its content, a model
    // retelling say, waits for this rather than for the page.
    if (next) onOpen?.()
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <div
        ref={body}
        // The same glide the rest of the app opens with, on the one property
        // that actually changes here, since maxHeight and overflow are not
        // grid-template-rows: the mask fade above already told the eye there
        // was more, and a snap once pressed would contradict that.
        style={{
          transition: 'max-height calc(var(--motion-base-ms) * 1ms) ease',
          ...(open ? { maxHeight: '100em' } : {
          maxHeight: height ?? `${lines * 1.75}em`,
          overflow: 'hidden',
          // The last line fades out rather than being sliced through, which is
          // what makes the cut look meant. Mask, not a gradient laid over it:
          // an overlay has to know the colour behind it, and this sits on three
          // different surfaces.
          //
          // Only where something is actually being held back. The fade is over
          // the bottom of the box, not the bottom of the words, so on a passage
          // shorter than the cut it dimmed the last line of a passage that was
          // already whole and said "there is more" about nothing.
          ...(cut ? {
            maskImage: 'linear-gradient(to bottom, #000 60%, transparent 100%)',
            WebkitMaskImage: 'linear-gradient(to bottom, #000 60%, transparent 100%)',
          } : {}),
          }),
        }}
      >
        {children}
      </div>

      {(cut || open) && (
        <button
          type="button"
          onClick={reveal}
          aria-expanded={open}
          style={{ '--c': accent }}
          className="type-small text-[var(--text-faint)] hover:text-[var(--c)] transition-colors"
        >
          {open ? less : more}
        </button>
      )}
    </div>
  )
}
