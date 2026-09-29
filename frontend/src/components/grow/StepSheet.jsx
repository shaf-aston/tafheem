/**
 * One step's practice card. It grows out of the circle that was tapped and
 * shrinks back into it, so the map never feels left; Escape or the scrim
 * closes it, and Tab stays inside it while it is open.
 *
 * This file is the dialog shell: the heading, the picture, and the focus and
 * close handling. What is inside an open step is grow/Practice.jsx.
 * A step in a locked tier, or a proposed topic that is not built yet, gets the
 * same card with the reason it is shut instead of a microphone.
 */
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'

import { nodeState } from '../../lib/grow'
import { byHand } from '../../lib/growKinds'
import { sayIn } from '../../lib/say'
import ArabicText from '../ui/ArabicText'
import Practice from './Practice'
import { StateIcon } from './icons'

const say = sayIn('en')
const FOCUSABLE = 'button, summary, input, select, textarea, [href], [tabindex]:not([tabindex="-1"])'

const CHIP = {
  learnt: ['grow-chip-done', say('Learnt')],
  started: ['grow-chip-now', say('In progress')],
  open: ['', say('Ready to start')],
  locked: ['', say('Locked')],
}

export default function StepSheet({ step, from, state, figure, tier, before, record, accent, onRecited, onDone, onGo, onClosed }) {
  const box = useRef(null)
  const closeRef = useRef(null)
  const [closing, setClosing] = useState(false)
  // Bumped each time a run makes the step learnt; the key replays the bloom.
  const [bloom, setBloom] = useState(0)
  const shown = state === 'locked' ? 'locked' : nodeState([step], record)

  // Where the card grows out of and goes back to: the centre of the circle.
  const aim = useCallback(() => {
    const at = from.isConnected ? from.getBoundingClientRect() : null
    const el = box.current
    el.style.setProperty('--dx', `${at ? at.left + at.width / 2 - innerWidth / 2 : 0}px`)
    el.style.setProperty('--dy', `${at ? at.top + at.height / 2 - innerHeight / 2 : 0}px`)
  }, [from])
  useLayoutEffect(aim, [aim])

  const closer = useRef(0)
  useEffect(() => () => clearTimeout(closer.current), [])
  const close = useCallback(() => {
    if (closer.current) return
    aim()
    setClosing(true)
    // As long as the shrink takes, read off the token the stylesheet uses.
    const ms = Number.parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--motion-spring-ms')) || 0
    closer.current = setTimeout(onClosed, ms)
  }, [aim, onClosed])

  useEffect(() => {
    closeRef.current.focus()
    const { overflow } = document.body.style
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = overflow
      if (from.isConnected) from.focus()
    }
  }, [from])

  useEffect(() => {
    const onKey = (event) => {
      if (event.key === 'Escape') close()
      else if (event.key === 'Tab') {
        const items = [...box.current.querySelectorAll(FOCUSABLE)].filter((el) => !el.disabled)
        const first = items[0]
        const last = items[items.length - 1]
        const at = document.activeElement
        if (!box.current.contains(at)) { event.preventDefault(); first.focus() }
        else if (event.shiftKey && at === first) { event.preventDefault(); last.focus() }
        else if (!event.shiftKey && at === last) { event.preventDefault(); first.focus() }
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [close])

  const [chipClass, chipText] = step.proposed
    ? ['', `${say('Proposed')} · ${tier.title}`]
    : CHIP[shown]

  return (
    <>
      <div className="grow-scrim" data-closing={closing ? '' : undefined} onMouseDown={close} />
      <div
        ref={box}
        role="dialog"
        aria-modal="true"
        aria-labelledby="grow-sheet-title"
        className="grow-sheet"
        data-closing={closing ? '' : undefined}
      >
        <div className="grow-sh-top">
          <h3 id="grow-sheet-title">{step.title}</h3>
          <button ref={closeRef} type="button" className="grow-x" aria-label={say('Close')} onClick={close}>
            <span aria-hidden="true">×</span>
          </button>
        </div>
        <span className={`grow-chip ${chipClass}`}>{chipText}</span>

        <div key={bloom} className={`grow-stage${bloom ? ' grow-go' : ''}`} aria-hidden="true">
          <div className="grow-fan">
            {Array.from({ length: 8 }, (_, k) => <i key={k} style={{ '--a': k * 45, '--k': k }} />)}
          </div>
          <div className={`grow-node ${byHand(step) ? 'grow-act' : 'grow-leaf'}`} data-s={shown}>
            <span className="grow-in"><StateIcon state={shown} figure={byHand(step) ? figure : null} /></span>
          </div>
        </div>

        {shown === 'locked' ? (
          <>
            {step.arabic && <ArabicText as="p" size="lg" className="block text-center leading-loose">{step.arabic}</ArabicText>}
            {step.meaning && <p className="grow-meaning">{step.meaning}</p>}
            <p className="grow-note">
              {before
                ? say(step.proposed
                  ? 'Locked until {before} is learnt. Shown here as a proposal for the {tier} tier.'
                  : 'Locked until {before} is learnt.', { before: before.title, tier: tier.title })
                : say('Not open yet.')}
            </p>
          </>
        ) : (
          <Practice
            key={step.id}
            step={step}
            record={record}
            accent={accent}
            onRecited={onRecited}
            onDone={onDone}
            onGo={onGo}
            onBloom={() => setBloom((n) => n + 1)}
          />
        )}
      </div>
    </>
  )
}
