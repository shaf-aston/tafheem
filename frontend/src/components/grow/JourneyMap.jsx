/**
 * Grow's map: a vine climbing through one raised plate per tier. Each node on
 * the vine is a group of steps (Standing, Bowing, Surahs 1); tap one and its
 * steps grow out sideways as a branch while the vine shifts left to make room.
 *
 * Presentation only. Where a node stands is lib/grow.js's nodeState, what is
 * on the map is grow.json and paths.json, and pressing a step is handed up:
 * this file knows nothing of the microphone, the record or the network.
 *
 * Motion is all from the theme's motion tokens (grow.css), so the Animations
 * setting and prefers-reduced-motion switch it off with everything else. The
 * one piece of motion decided here is the tier unlock, which is a sequence
 * (gate opens, dotted path draws, vine grows), so it is stepped in `beat`s.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

import config from '../../grow.json'
import { groupsOf, nodeState, unlocked } from '../../lib/grow'
import { sayIn } from '../../lib/say'
import ArabicText from '../ui/ArabicText'
import Mascot from '../ui/Mascot'
import { GroupIcon, Flower, StateIcon } from './icons'
import './grow.css'

const say = sayIn('en')
const WORDS = {
  learnt: say('learnt'),
  started: say('in progress'),
  open: say('ready to start'),
  locked: say('locked'),
}
const BEATS = config['unlock-ms']

/** No motion wanted: the reader's own setting, or the Animations switch. */
const still = () =>
  globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches ||
  Number(getComputedStyle(document.documentElement).getPropertyValue('--motion-scale')) === 0

/** How much of a group is learnt, as a ring round its node. */
function Ring({ fraction }) {
  return (
    <svg viewBox="0 0 100 100" className="grow-ring" aria-hidden="true">
      <circle className="grow-ring-t" cx="50" cy="50" r="46" />
      {fraction > 0 && (
        <circle
          className="grow-ring-f"
          cx="50" cy="50" r="46" pathLength="1"
          strokeDasharray={`${fraction} 1`}
          transform="rotate(-90 50 50)"
        />
      )}
    </svg>
  )
}

function Item({ step, i, state, now, days, onOpen }) {
  return (
    <div className="grow-item" style={{ '--i': i }}>
      <div className="grow-nw">
        <button
          type="button"
          className={`grow-node grow-leaf${i % 2 ? ' grow-alt' : ''}${now ? ' grow-pulse' : ''}`}
          data-s={state}
          data-now={now ? '' : undefined}
          aria-label={`${step.title}, ${WORDS[state]}`}
          onClick={(event) => onOpen(step, event.currentTarget, state)}
        >
          <span className="grow-in"><StateIcon state={state} /></span>
        </button>
      </div>
      <span className="grow-lbl">
        {step.title}
        {now && <><br />{days}</>}
      </span>
    </div>
  )
}

function Row({ group, open, isOpen, record, next, mood, onToggle, onStep }) {
  const steps = group.steps
  const state = nodeState(steps, record, open)
  const learnt = steps.filter((step) => nodeState([step], record, open) === 'learnt').length
  const now = open && next != null && steps.includes(next)

  return (
    <div className={`grow-row${isOpen ? ' grow-row-open' : ''}`} data-now={now ? '' : undefined}>
      <div className="grow-cell">
        <div className="grow-nw">
          <button
            type="button"
            className={`grow-node grow-gnode${now ? ' grow-pulse' : ''}`}
            data-s={state}
            data-group={group.id}
            aria-expanded={isOpen}
            aria-controls={`grow-ln-${group.id}`}
            aria-label={`${group.title}, ${learnt} of ${steps.length} ${say('learnt')}, ${WORDS[state]}`}
            onClick={(event) => onToggle(group.id, event.currentTarget)}
          >
            {state !== 'locked' && <Ring fraction={learnt / steps.length} />}
            <span className="grow-in">{state === 'learnt' ? <Flower sway /> : <GroupIcon name={group.icon} />}</span>
            <span className="grow-cnt" aria-hidden="true">{learnt}/{steps.length}</span>
          </button>
          {now && <Mascot place="map" mood={mood} className="grow-qalam" />}
        </div>
        <span className="grow-gl">
          {group.title}
          {group.arabic && <ArabicText size="sm" className="grow-gl-ar">{group.arabic}</ArabicText>}
        </span>
      </div>
      <div className="grow-lane" id={`grow-ln-${group.id}`} role="group" aria-label={`${group.title}, ${say('steps')}`}>
        <div className="grow-lane-in">
          <svg className="grow-branch" aria-hidden="true">
            <line x1="0" y1="48" x2="100%" y2="48" pathLength="1" />
          </svg>
          {steps.map((step, i) => {
            const cleanDays = record[step.id]?.cleanDays?.length ?? 0
            return (
              <Item
                key={step.id}
                step={step}
                i={i}
                state={nodeState([step], record, open)}
                now={step === next}
                days={say('{done} of {need} days', { done: cleanDays, need: config['clean-days'] })}
                onOpen={(picked, el, at) => onStep(picked, { el, group, state: at })}
              />
            )
          })}
        </div>
      </div>
    </div>
  )
}

/**
 * One tier. A tier that has just opened plays its unlock: `beat` counts the
 * stages, 1 the shut gate, 2 the gate opening, 3 the dotted path drawing, 4 the
 * vine growing and the groups appearing, then it hands the first group up to
 * be opened. Between beats it still looks locked, so nothing shows early.
 */
function Plate({ tier, i, open, openId, record, next, mood, onToggle, onStep, onGrown }) {
  const groups = groupsOf(tier)
  const first = groups[0].id
  const [was, setWas] = useState(open)
  const [beat, setBeat] = useState(0)
  const plate = useRef(null)

  // Told during render, not in an effect: the plate must look locked from the
  // very frame `open` turns true, or the tier would flash open before the gate.
  if (open !== was) {
    setWas(open)
    if (open && !still()) setBeat(1)
  }

  useEffect(() => {
    if (!beat) return undefined
    if (beat === 1) plate.current?.scrollIntoView({ block: 'center', behavior: 'smooth' })
    const wait = setTimeout(() => {
      if (beat < BEATS.length) return setBeat(beat + 1)
      setBeat(0)
      return onGrown(first)
    }, BEATS[beat - 1])
    return () => clearTimeout(wait)
  }, [beat, first, onGrown])

  const locked = !open || (beat > 0 && beat < BEATS.length)
  const cls = ['grow-plate']
  if (locked) cls.push('grow-locked')
  if (beat) cls.push('grow-pre')
  if (beat >= 2) cls.push('grow-u1')
  if (beat >= 3) cls.push('grow-u2')
  if (beat >= 4) cls.push('grow-u3')

  return (
    <section ref={plate} className={cls.join(' ')} aria-labelledby={`grow-h-${tier.id}`}>
      {(!open || beat > 0) && (
        <div className="grow-gate" aria-hidden="true">
          <span className="grow-door grow-door-l" />
          <span className="grow-door grow-door-r" />
          <span className="grow-light" />
        </div>
      )}
      <div className="grow-hd">
        <div className="grow-hn"><span className="grow-n">{i + 1}</span></div>
        <div className="grow-ht">
          <h2 id={`grow-h-${tier.id}`}>
            {tier.title}
            {tier.arabic && <ArabicText size="sm" className="grow-h-ar">{tier.arabic}</ArabicText>}
          </h2>
          {locked && <span className="grow-tag">{tier.paths.length ? say('Locked') : say('Proposed, locked')}</span>}
        </div>
      </div>
      {groups.map((group) => (
        <Row
          key={group.id}
          group={group}
          open={open}
          isOpen={openId === group.id}
          record={record}
          next={next}
          mood={mood}
          onToggle={onToggle}
          onStep={(step, at) => onStep(step, { ...at, tier, i })}
        />
      ))}
    </section>
  )
}

export default function JourneyMap({ tiers, openId, record, next, mood, onToggle, onStep, onGrown }) {
  const toggle = useCallback((id, el) => {
    onToggle(id)
    if (openId !== id) el.closest('.grow-row')?.scrollIntoView({ block: 'nearest', behavior: still() ? 'auto' : 'smooth' })
  }, [onToggle, openId])

  return (
    <div className={`grow-map${openId ? ' grow-map-open' : ''}`}>
      {tiers.map((tier, i) => (
        <Plate
          key={tier.id}
          tier={tier}
          i={i}
          open={unlocked(tiers, i, record)}
          openId={openId}
          record={record}
          next={next}
          mood={mood}
          onToggle={toggle}
          onStep={onStep}
          onGrown={onGrown}
        />
      ))}
    </div>
  )
}
