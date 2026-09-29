/**
 * Grow, نَبَات: a path through what a person says in their prayer, one step at
 * a time, and an honest answer to "did I say it right?".
 *
 *   وَأَنبَتَهَا نَبَاتًا حَسَنًا (3:37), and He made her grow a good growth.
 *
 * Three promises decide everything on this page:
 *   1. No ruling is the app's own. The ear judges how a word was said, never
 *      what the prayer requires; what the prayer requires is quoted from a
 *      named scholar's book, word for word, and kept out of the way until
 *      asked for (tests/test_grow.py holds every quote to the book).
 *   2. "Not sure" is said when it is not sure, and it never counts as right.
 *   3. The score is what has been learnt, not what has been opened.
 *
 * Its own module, in three layers: the map (grow/JourneyMap) draws it, the
 * card (grow/StepSheet) practises one step, and this file holds the record
 * and the choices between them. The tiers are grow.json, the paths come from
 * /api/grow/paths, the marking and the record are lib/grow.js, and everything
 * else is the app's shared pieces, the same microphone, the same word
 * colours, the same ear checks, so nothing here changes how another tab behaves.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { growPathsQuery } from '../api'
import config from '../grow.json'
import { afterRecitation, currentGroup, reactionTo, score, tiersOf, upNext } from '../lib/grow'
import { moodFrom } from '../lib/mood'
import { recordAttempt } from '../lib/progress'
import { sayIn } from '../lib/say'
import { useRemembered } from '../lib/useRemembered'
import { useHealth } from '../lib/useHealth'
import ErrorAlert from './ui/ErrorAlert'
import SectionHeader from './ui/SectionHeader'
import JourneyMap from './grow/JourneyMap'
import StepSheet from './grow/StepSheet'

const say = sayIn('en')

export default function GrowPanel({ accent, onGo }) {
  const paths = useQuery(growPathsQuery)
  const { status } = useHealth()
  // The record is kept as JSON text in this browser only (useRemembered).
  const [saved, save] = useRemembered(config['storage-key'])
  const record = useMemo(() => JSON.parse(saved || '{}'), [saved])
  // Undefined until the map has drawn once, so the current group opens after
  // that first frame and grows out, rather than being open from the start.
  const [openId, setOpenId] = useState(undefined)
  const [sheet, setSheet] = useState(null)
  const [reaction, setReaction] = useState(null)
  const streak = useRef(0)

  const tiers = useMemo(() => tiersOf(config.tiers, paths.data), [paths.data])
  const next = useMemo(() => upNext(tiers, record), [tiers, record])
  const current = useMemo(() => currentGroup(tiers, next), [tiers, next])
  const done = score(tiers, record)

  useEffect(() => {
    if (!paths.data) return undefined
    const frame = requestAnimationFrame(() => requestAnimationFrame(() => setOpenId((was) => (was === undefined ? current : was))))
    return () => cancelAnimationFrame(frame)
  }, [paths.data, current])

  useEffect(() => {
    if (!reaction) return undefined
    const wait = setTimeout(() => setReaction(null), config['mood-ms'])
    return () => clearTimeout(wait)
  }, [reaction])

  // Escape shuts the open branch, unless the card is up: then it is the card's.
  useEffect(() => {
    const onKey = (event) => {
      if (event.key !== 'Escape' || sheet || !openId) return
      const node = document.querySelector(`[data-group="${openId}"]`)
      setOpenId(null)
      node.focus()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [sheet, openId])

  const toggle = useCallback((id) => setOpenId((was) => (was === id ? null : id)), [])
  const closed = useCallback(() => setSheet(null), [])

  function recited(clean) {
    const { step, group } = sheet
    streak.current = clean ? streak.current + 1 : 0
    save(JSON.stringify(afterRecitation(record, step.id, clean)))
    setReaction({ mood: reactionTo(clean, streak.current) })
    recordAttempt({ module: 'grow', item: `${group.path}/${step.id}`, correct: clean, context: { path: group.path } })
  }

  const mood = reaction?.mood ?? moodFrom({ offline: status === 'error' })

  return (
    <>
      <div className="panel" inert={Boolean(sheet)}>
        <SectionHeader
          title="Grow!"
          arabic="نَبَات"
          subtitle={say('Learn to say it right, one step at a time. The app listens and marks each word; the rulings are the scholars\'.')}
          aside={done.total > 0 && (
            <p className="grow-progress">
              <span className="tabular-nums">{say('{learnt} of {total} learnt', done)}</span>
              <span>{say('Only steps said right on {need} different days count', { need: config['clean-days'] })}</span>
              <span className="grow-bar" aria-hidden="true"><i style={{ width: `${(100 * done.learnt) / done.total}%` }} /></span>
            </p>
          )}
        />

        {paths.isError && <ErrorAlert title={say('Could not load the paths')}>{say('Check the connection and try again.')}</ErrorAlert>}

        {paths.data && (
          <JourneyMap
            tiers={tiers}
            openId={openId}
            record={record}
            next={next}
            mood={mood}
            onToggle={toggle}
            onGrown={setOpenId}
            onStep={(step, at) => setSheet({ step, ...at })}
          />
        )}
      </div>

      {sheet && (
        <StepSheet
          key={sheet.step.id}
          step={sheet.step}
          from={sheet.el}
          state={sheet.state}
          tier={sheet.tier}
          before={tiers[sheet.i - 1]}
          record={record}
          accent={accent}
          onRecited={recited}
          onGo={onGo}
          onClosed={closed}
        />
      )}
    </>
  )
}
