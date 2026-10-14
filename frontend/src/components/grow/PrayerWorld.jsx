/**
 * The Prayer world: a path through what a person says in their prayer, one
 * step at a time, and an honest answer to "did I say it right?".
 *
 *   وَأَنبَتَهَا نَبَاتًا حَسَنًا (3:37), and He made her grow a good growth.
 *
 * Three promises decide everything here:
 *   1. No ruling is the app's own. The ear judges how a word was said, never
 *      what the prayer requires; what the prayer requires is quoted from a
 *      named scholar's book, word for word, and kept out of the way until
 *      asked for (tests/test_grow.py holds every quote to the book).
 *   2. "Not sure" is said when it is not sure, and it never counts as right.
 *   3. The score is what has been learnt, not what has been opened.
 *
 * In three layers: the map (grow/GrowMap) draws it, the card (grow/StepSheet)
 * practises one step, and this file holds the choices between them. The
 * record and the paths are lib/usePrayerRecord.js, shared with Grow's home;
 * the marking is lib/grow.js; everything else is the app's shared pieces, the
 * same microphone, the same word colours, the same ear checks.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

import config from '../../grow.json'
import { afterDone, afterRecitation, reactionTo } from '../../lib/grow'
import { moodFrom } from '../../lib/mood'
import { recordAttempt } from '../../lib/progress'
import { sayIn } from '../../lib/say'
import { useHealth } from '../../lib/useHealth'
import ErrorAlert from '../ui/ErrorAlert'
import GrowMap from './GrowMap'
import StepSheet from './StepSheet'
import WorldHeader from './WorldHeader'

const say = sayIn('en')

export default function PrayerWorld({ world, accent, onGo, onBack, prayer }) {
  const { paths, record, keep, tiers, next, done } = prayer
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
      <div inert={Boolean(sheet)} style={{ '--c': accent }}>
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
        <StepSheet
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
