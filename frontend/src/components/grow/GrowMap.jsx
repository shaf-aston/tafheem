/**
 * Grow's map: one plate per tier, a gate on each tier not yet open. Inside a
 * tier each path has a trunk down its left; every group is a bud on it with
 * its steps growing out as a branch. A long branch takes a whole line; short
 * ones share a line and curl into the room they get, so no line is left half
 * empty. A group of one step is just that step, named by its group. A group
 * marked `alongside` (wudu's good manners) runs through its whole path, so it
 * is one big leaf beside the path, not a branch after the one before.
 *
 * Presentation only: states come from lib/grow.js's mapOf, the shape from
 * grow.json's vine, and pressing a step is handed up with where it was
 * pressed, so the practice card can grow out of it.
 */
import { useLayoutEffect, useMemo } from 'react'

import config from '../../grow.json'
import { mapOf } from '../../lib/grow'
import { sayIn } from '../../lib/say'
import ArabicText from '../ui/ArabicText'
import { useUnlock, useWidth } from './hooks'
import { Bud, GroupLabel, Step } from './Step'
import Vine from './Vine'

const say = sayIn('en')
const { cell: CELL, bud: BUD } = config.vine

/** One group: its bud and its branch, or, with one step, that step alone. */
function Branch({ one, mood, onPress }) {
  const { group, steps } = one
  if (steps.length === 1) {
    return (
      <div className="grow-branch grow-single" style={{ '--basis': `${BUD}px` }}>
        <div className="grow-knot">
          <Step one={steps[0]} group={group} k={0} mood={mood} label={<GroupLabel group={group} />} onPress={onPress} />
        </div>
      </div>
    )
  }
  return (
    <div className="grow-branch" style={{ '--basis': `${BUD + steps.length * CELL}px` }}>
      <div className="grow-knot">
        <Bud one={one} onPress={onPress} />
        <GroupLabel group={group} />
      </div>
      <Vine
        from
        items={steps.map((each, k) => ({ key: each.step.id, node: <Step one={each} group={group} k={k} mood={mood} onPress={onPress} /> }))}
      />
    </div>
  )
}

/**
 * A path's branches. Where the page wraps them depends on its width, so a
 * branch that lands mid-line is found after layout and marked `data-joined`,
 * which draws the stem joining it to the branch before.
 */
function Branches({ groups, mood, onPress }) {
  const [ref, width] = useWidth()
  useLayoutEffect(() => {
    for (const el of ref.current.children) el.toggleAttribute('data-joined', el.offsetLeft > 0)
  }, [ref, width, groups])
  return (
    <div ref={ref} className="grow-branches">
      {groups.map((one) => <Branch key={one.group.id} one={one} mood={mood} onPress={onPress} />)}
    </div>
  )
}

/** A group that runs through its whole path: one big leaf, its steps inside. */
function Alongside({ one, mood, onPress }) {
  const { group, steps, state } = one
  return (
    <aside className="grow-alongside" data-s={state} aria-label={`${group.title}, ${say('throughout')}`}>
      <div className="grow-alongside-hd">
        <Bud one={one} onPress={onPress} />
        <div>
          <h3>{group.title}</h3>
          {group.arabic && <ArabicText size="sm">{group.arabic}</ArabicText>}
          <span className="grow-tag">{say('Throughout')}</span>
        </div>
      </div>
      <div className="grow-alongside-steps">
        {steps.map((each, k) => (
          <div key={each.step.id} className="grow-spot-in">
            <Step one={each} group={group} k={k} mood={mood} onPress={onPress} />
          </div>
        ))}
      </div>
    </aside>
  )
}

function Tier({ row, mood, onStep }) {
  const { tier, i, open, paths, learnt, total } = row
  const { beat, plays } = useUnlock(open)
  const press = (step, el, state, group) => onStep(step, { el, group, state, tier, i })
  const cls = ['grow-tier']
  if (!open || beat) cls.push('grow-locked')
  if (beat >= 2) cls.push('grow-u1')
  return (
    <section className={cls.join(' ')} aria-labelledby={`grow-h-${tier.id}`}>
      {(!open || beat > 0) && (
        <div className="grow-gate" aria-hidden="true">
          <span className="grow-door grow-door-l" />
          <span className="grow-door grow-door-r" />
          <span className="grow-light" />
        </div>
      )}
      <header className="grow-hd">
        <span className="grow-n">{i + 1}</span>
        <h2 id={`grow-h-${tier.id}`}>{tier.title}</h2>
        <span className="grow-tag">
          {open ? say('{learnt} of {total} learnt', { learnt, total }) : say(tier.paths.length ? 'Locked' : 'Proposed, locked')}
        </span>
      </header>
      {(beat === 0 || beat > 2) && (
        <div key={plays} className="grow-body">
          {paths.map(({ path, groups, alongside }) => (
            <div key={path.id} className="grow-path" data-alongside={alongside.length ? '' : undefined}>
              <div className="grow-trunk">
                {path.title && (
                  <p className="grow-sign">{path.title} {path.arabic && <ArabicText size="sm">{path.arabic}</ArabicText>}</p>
                )}
                <Branches groups={groups} mood={mood} onPress={press} />
              </div>
              {alongside.map((one) => <Alongside key={one.group.id} one={one} mood={mood} onPress={press} />)}
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

export default function GrowMap({ tiers, record, next, mood, onStep }) {
  const rows = useMemo(() => mapOf(tiers, record, next), [tiers, record, next])
  return (
    <div className="grow-map" style={{ '--knot': `${BUD}px` }}>
      {rows.map((row) => <Tier key={row.tier.id} row={row} mood={mood} onStep={onStep} />)}
    </div>
  )
}
