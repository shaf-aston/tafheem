/**
 * The launcher behind the pen: every tab at once, as satellites round an orb.
 *
 * Nothing here is a list. The panels sit on a ring in their own colours
 * and the arrow keys spin the ring rather than walking a column, which is the
 * whole point of it: on a page you are inside one tab, here you are above all
 * of them. Typing turns the same ring into a search, because the orb holds the
 * same command line the header does.
 *
 * A native <dialog>, the same as Settings, so Esc, the backdrop and focus
 * trapping are the browser's job and not hand-written.
 */
import { useEffect, useRef, useState } from 'react'

import { useCommandLine } from '../../lib/useCommandLine'
import { isArabic } from '../../lib/arabicText'
import { moodFrom } from '../../lib/mood'
import ArabicText from './ArabicText'
import CommandField from './CommandField'
import CommandResults from './CommandResults'
import Mascot from './Mascot'

const NAME = 'sh'

export default function SpatialHome({ open, onClose, tabs, colorOf, onGo, here }) {
  const dialog = useRef(null)
  const input = useRef(null)

  // Which satellite the ring is turned to. Counted as steps rather than held as
  // an index, so spinning past the last one keeps turning the same way instead
  // of unwinding all the way back round.
  const [steps, setSteps] = useState(0)
  // Where the ring stood when it opened. The arrival is staggered outwards from
  // here, and it must not move once the dance has begun, which spinning would
  // do if the stagger were counted from wherever the selection is now.
  const [startAt, setStartAt] = useState(0)
  const count = tabs.length
  const selected = ((steps % count) + count) % count
  const spin = (by) => setSteps((current) => current + by)

  const line = useCommandLine(tabs, (row) => {
    onClose()
    onGo(row.tabId, row.value)
  }, {
    // The keys the line has no use for are this ring's: the arrows spin it
    // (only while no list is showing; the hook owns that rule) and Enter with
    // nothing typed opens the tab it is turned to. Escape is left out on
    // purpose so the dialog closes natively.
    onSpin: spin,
    onEnter: () => { onClose(); onGo(tabs[selected].id) },
  })
  const { query, rows, active, setActive, type, run } = line

  // Every opening starts fresh: an empty line, and the ring already turned to
  // where the reader is, in that tab's colour. It used to open on the first tab
  // whatever page it was called from, which said the wrong thing twice, the ring
  // pointing elsewhere and the orb wearing another tab's colour. Reset while
  // rendering, the same idiom the panels use for a prop their state follows.
  const [wasOpen, setWasOpen] = useState(open)
  if (open !== wasOpen) {
    setWasOpen(open)
    if (open) {
      type('')
      const at = Math.max(0, tabs.findIndex((tab) => tab.id === here))
      setSteps(at)
      setStartAt(at)
    }
  }

  useEffect(() => {
    const element = dialog.current
    if (!element) return
    if (open && !element.open) {
      element.showModal()
      input.current?.focus()
    }
    if (!open && element.open) element.close()
  }, [open])

  const go = (id, value = null) => { onClose(); onGo(id, value) }

  // A tab still standing after what has been typed. Everything is lit while the
  // line is empty, which is the resting state of the ring.
  const lit = (id) => !query || rows.some((row) => row.tabId === id)

  // Which way the two halves stand. Nothing typed means neither has moved and
  // the ring is in the middle. Once there are answers they take the side the
  // language runs towards, so English opens them on the right and Arabic on the
  // left. The "/" and "@" a reader may type first are Latin punctuation, so the
  // side follows any Arabic letter in the line, so "@كتب" counts as Arabic
  // even though it opens with a Latin mark.
  const side = rows.length === 0 ? 'none' : (isArabic(query) ? 'rtl' : 'ltr')

  return (
    <dialog
      ref={dialog}
      onClose={onClose}
      onClick={(e) => e.target === dialog.current && onClose()}
      aria-label="Everything, at once"
      className="sh-dialog"
    >
      <div className="sh-stage" onClick={(e) => e.stopPropagation()}>
        {/* Two halves that slide apart the moment there is something to show.
            Which half goes where follows the language being typed, so the
            answers always open on the side that language runs towards and the
            reader's eye leaves the box in the direction it is already going. */}
        <div className="sh-pair" data-side={side}>
        <div className="sh-ring">
        <div className="sh-orbit" style={{ '--turn': `${-steps * (360 / count)}deg` }}>
          <span className="sh-track" aria-hidden="true" />

          {tabs.map((tab, i) => {
            const angle = i * (360 / count)
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => go(tab.id)}
                // Deliberately no hover here. Turning the ring towards whatever
                // is under the pointer slides the next satellite into that same
                // spot, which hovers itself, which turns the ring again: the
                // whole thing chases the cursor and never settles. Hover lights
                // a satellite up in CSS and moves nothing; the arrows spin.
                className="sh-sat dance"
                data-selected={i === selected ? 'true' : undefined}
                data-dim={lit(tab.id) ? undefined : 'true'}
                aria-current={i === selected ? 'true' : undefined}
                // Dimmed means "what you typed rules this one out". Said in the
                // markup as well as in the colour, so it is not colour alone.
                aria-disabled={lit(tab.id) ? undefined : 'true'}
                // --i is the order the arrival walks, counted from the tab the
                // reader is already in, so the dance starts where they are and
                // goes round the clock from there rather than always at the
                // first tab.
                style={{
                  '--c': colorOf(tab.id),
                  '--a': `${angle}deg`,
                  '--i': (i - startAt + count) % count,
                }}
              >
                <span className="sh-sat-mark" aria-hidden="true">
                  <ArabicText size="sm">{tab.mark}</ArabicText>
                </span>
                <span className="sh-sat-label">{tab.label}</span>
                <ArabicText size="sm" className="sh-sat-arabic">{tab.arabic}</ArabicText>
              </button>
            )
          })}

          <div className="sh-orb dance" style={{ '--c': colorOf(tabs[selected].id) }}>
            <Mascot mood={moodFrom({})} place="orb" />
            {/* The header's own box, not a second one that looks like it: same
                glass, same grey completion ahead of the cursor, same rounded
                edge. No Ctrl K badge, because the shortcut that opens this is
                already what the reader just pressed. */}
            <CommandField
              line={line}
              name={NAME}
              inputRef={input}
              placeholder="Search or ask"
              showing={rows.length > 0}
            />
          </div>
        </div>
        </div>

          <div className="sh-panel">
            {rows.length > 0 && (
              <CommandResults
                id={`${NAME}-results`}
                name={NAME}
                rows={rows}
                tabs={tabs}
                colorOf={colorOf}
                active={active}
                onHover={setActive}
                onPick={run}
                railTab={rows[active]?.tabId}
                onRail={(id) => go(id)}
              />
            )}
          </div>
        </div>

        {rows.length === 0 && (
          <p className="sh-hint">
            <kbd>←</kbd> <kbd>→</kbd> spin · <kbd>Enter</kbd> open{' '}
            {/* Spun with the arrows, the ring moving is the only thing that says
                which tab Enter would open. Spoken here so it is not sight only. */}
            <span className="sh-hint-tab" aria-live="polite">{tabs[selected].label}</span>
            {' '}· <kbd>Esc</kbd> close
          </p>
        )}
      </div>
    </dialog>
  )
}
