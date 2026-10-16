/**
 * A path world: the step map (GrowMap) + practice card (CardSheet). Record: lib/usePathRecord.js; marking: lib/grow.js.
 * Rules: rulings are quoted from named books (tests/test_grow.py); "not sure" never counts; score = learnt steps only.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

import config from '../../grow.json'
import { afterDone, afterRecitation, reactionTo } from '../../lib/grow'
import { moodFrom } from '../../lib/mood'
import { recordAttempt } from '../../lib/progress'
import { sayIn } from '../../lib/say'
import { useHealth } from '../../lib/useHealth'
import ErrorAlert from '../ui/ErrorAlert'
import Backdrop from './Backdrop'
import GrowMap from './GrowMap'
import CardSheet from './CardSheet'
import WorldHeader from './WorldHeader'

const say = sayIn('en')

export default function PathWorld({ world, accent, onGo, onBack, state }) {
  const { paths, record, keep, tiers, next, done } = state
  const { status } = useHealth()
  const [sheet, setSheet] = useState(null)
  const [reaction, setReaction] = useState(null)
  const streak = useRef(0)

  useEffect(() => {
    if (!reaction) return undefined
    const wait = setTimeout(() => setReaction(null), config['mood-ms'])
    return () => clearTimeout(wait)
  }, [reaction])

  const closed = useCallback(() => setSheet(null), [])

  function recited(clean) {
    const { step, group } = sheet
    streak.current = clean ? streak.current + 1 : 0
    keep(afterRecitation(record, step.id, clean))
    setReaction({ mood: reactionTo(clean, streak.current) })
    recordAttempt({ module: 'grow', item: `${group.path}/${step.id}`, correct: clean, context: { path: group.path } })
  }

  // A posture is ticked off by the reader: learnt at once, and it counts as right.
  function doneByHand() {
    const { step, group } = sheet
    streak.current += 1
    keep(afterDone(record, step.id))
    setReaction({ mood: reactionTo(true, streak.current) })
    recordAttempt({ module: 'grow', item: `${group.path}/${step.id}`, correct: true, context: { path: group.path } })
  }

  const mood = reaction?.mood ?? moodFrom({ offline: status === 'error' })

  return (
    <>
      <div className="grow-world" inert={Boolean(sheet)} style={{ '--c': accent }}>
        <Backdrop id={world.backdrop} />
        <WorldHeader world={world} onBack={onBack}>
          {done.total > 0 && (
            <p className="grow-progress">
              <span className="tabular-nums">{say('{learnt} of {total} learnt', done)}</span>
              <span>{say('Only steps said right on {need} different days count', { need: config['clean-days'] })}</span>
              <span className="grow-bar" aria-hidden="true"><i style={{ width: `${(100 * done.learnt) / done.total}%` }} /></span>
            </p>
          )}
        </WorldHeader>

        {paths.isError && <ErrorAlert title={say('Could not load the paths')} error={paths.error} onRetry={paths.refetch} />}

        {paths.data && (
          <GrowMap tiers={tiers} record={record} next={next} mood={mood} onStep={(step, at) => setSheet({ step, ...at })} />
        )}
      </div>

      {sheet && (
        <CardSheet
          key={sheet.step.id}
          step={sheet.step}
          from={sheet.el}
          state={sheet.state}
          figure={sheet.group.icon}
          tier={sheet.tier}
          before={tiers[sheet.i - 1]}
          record={record}
          accent={accent}
          onRecited={recited}
          onDone={doneByHand}
          onGo={onGo}
          onClosed={closed}
        />
      )}
    </>
  )
}
