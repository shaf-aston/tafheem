/**
 * Grow's map: a vine climbing through one raised plate per tier. Each node on
 * the vine is a group of steps (Standing, Bowing, Surahs 1); tap one and its
 * steps grow out sideways as a branch while the vine shifts left to make room.
 *
 * Presentation only. Where a node stands is lib/grow.js's nodeState, what is
 * on the map is grow.json and paths.json, and pressing a step is handed up:
 * this file knows nothing of the microphone, the record or the network.
 *
 * The vine winds in soft S-curves, one per row, and a branch grows out as a
 * curving twig per step, drawn on as its step pops in (grow.css). Motion is all
 * from the theme's motion tokens, so the Animations setting and
 * prefers-reduced-motion switch it off with everything else. The
 * one piece of motion decided here is the tier unlock, which is a sequence
 * (gate opens, vine draws, groups appear), so it is stepped in `beat`s.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

import config from '../../grow.json'
import { daysOf, groupsOf, nodeState, unlocked } from '../../lib/grow'
import { scrollToEl } from '../../lib/scrollToEl'
import { sayIn } from '../../lib/say'
import ArabicText from '../ui/ArabicText'
import { byHand } from '../../lib/growKinds'
import Mascot from '../ui/Mascot'
import MicMark from '../ui/MicMark'
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
const { step: STEP, node: NODE, sway: SWAY, tail: TAIL } = config.branch
// Rows and steps lean opposite ways in turn: -1 up, 1 down, 0 for the group's own circle.
const lean = (i) => (i < 0 ? 0 : i % 2 ? 1 : -1)

/** No motion wanted: the reader's own setting, or the Animations switch. Only the unlock sequence, which JS times, asks. */
const still = () =>
  matchMedia('(prefers-reduced-motion: reduce)').matches ||
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

/** The stretch of branch from the step before to this one, drawn on as it grows; the last runs a little past. */
function Twig({ i, last }) {
  const from = NODE / 2 + lean(i - 1) * SWAY
  const to = NODE / 2 + lean(i) * SWAY
  return (
    <svg className="grow-twig" width={STEP} height={NODE} viewBox={`0 0 ${STEP} ${NODE}`} aria-hidden="true">
      <path d={`M0 ${from}C${STEP / 2} ${from} ${STEP / 2} ${to} ${STEP} ${to}${last ? `h${TAIL}` : ''}`} pathLength="1" />
    </svg>
  )
}

function Item({ step, i, last, state, now, days, figure, onOpen }) {
  const act = byHand(step)
  return (
    <div className="grow-item" style={{ '--i': i, '--w': lean(i) }}>
      <Twig i={i} last={last} />
      <div className="grow-nw">
        <button
          type="button"
          className={`grow-node ${act ? 'grow-act' : `grow-leaf${i % 2 ? ' grow-alt' : ''}`}${now ? ' grow-pulse' : ''}`}
          data-s={state}
          data-now={now ? '' : undefined}
          aria-label={`${step.title}, ${WORDS[state]}`}
          onClick={(event) => onOpen(step, event.currentTarget, state)}
        >
          <span className="grow-in"><StateIcon state={state} figure={act ? figure : null} /></span>
          {!act && state !== 'learnt' && <MicMark size={12} className="grow-say" />}
        </button>
      </div>
      <span className="grow-lbl">
        {step.title}
        {now && !act && <><br />{days}</>}
      </span>
    </div>
  )
}

function Row({ group, index, open, isOpen, record, next, mood, onToggle, onStep }) {
  const steps = group.steps
  const state = nodeState(steps, record, open)
  const learnt = steps.filter((step) => nodeState([step], record, open) === 'learnt').length
  const now = open && steps.includes(next)

  return (
    <div className={`grow-row${isOpen ? ' grow-row-open' : ''}`} data-now={now ? '' : undefined}>
      <svg className="grow-stem" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <path d={index % 2 ? 'M50 0V58C10 63 10 80 50 88V100' : 'M50 0V58C90 63 90 80 50 88V100'} pathLength="1" />
      </svg>
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
            <span className="grow-in">{state === 'learnt' ? <Flower /> : <GroupIcon name={group.icon} />}</span>
            <span className="grow-cnt" aria-hidden="true">{learnt}/{steps.length}</span>
          </button>
          {now && <Mascot place="map" mood={mood} className="grow-qalam" />}
        </div>
        <span className="grow-gl">
          {group.title}
          {group.arabic && <ArabicText size="sm" className="grow-gl-ar">{group.arabic}</ArabicText>}
        </span>
      </div>
      <div
        className="grow-lane"
        id={`grow-ln-${group.id}`}
        role="group"
        aria-label={`${group.title}, ${say('steps')}`}
        style={{ '--iw': `${STEP}px`, '--n': `${NODE}px`, '--sway': SWAY }}
      >
        <div className="grow-lane-in">
          {steps.map((step, i) => (
            <Item
              key={step.id}
              step={step}
              i={i}
              last={i === steps.length - 1}
              figure={group.icon}
              state={nodeState([step], record, open)}
              now={step === next}
              days={say('{done} of {need} days', { done: daysOf(record, step.id), need: config['clean-days'] })}
              onOpen={(picked, el, at) => onStep(picked, { el, group, state: at })}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

/**
 * One tier. A tier that has just opened plays its unlock: `beat` counts the
 * stages, 1 the shut gate, 2 the gate opening, 3 the vine drawing, 4 the
 * groups appearing, then it hands the first group up to be opened. Between beats it still looks locked, so nothing shows early.
 */
function Plate({ tier, i, open, openId, record, next, mood, onToggle, onStep, onGrown }) {
  const groups = groupsOf(tier)
  const first = groups[0]?.id
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
    if (beat === 1) scrollToEl(plate.current, 'center')
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
        <span className="grow-stub" />
        <div className="grow-hn"><span className="grow-n">{i + 1}</span></div>
        <div className="grow-ht">
          <h2 id={`grow-h-${tier.id}`}>
            {tier.title}
            {tier.arabic && <ArabicText size="sm" className="grow-h-ar">{tier.arabic}</ArabicText>}
          </h2>
          {locked && <span className="grow-tag">{tier.paths.length ? say('Locked') : say('Proposed, locked')}</span>}
        </div>
      </div>
      {groups.map((group, index) => (
        <Row
          key={group.id}
          group={group}
          index={index}
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
    if (openId !== id) scrollToEl(el.closest('.grow-row'), 'nearest')
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
