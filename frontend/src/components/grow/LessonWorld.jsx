/** A lessons world (Words, Hadith): stages by items learnt (the server's "known") and a lesson button. `state` from lib/useLessonWorld.js. */
import { sayIn } from '../../lib/say'
import ErrorAlert from '../ui/ErrorAlert'
import PrimaryButton from '../ui/PrimaryButton'
import { Skeleton } from '../ui/Skeleton'
import WorldHeader from './WorldHeader'

const say = sayIn('en')

export default function LessonWorld({ world, accent, state: lessons, onBack, onStart }) {
  return (
    <div style={{ '--w': accent }}>
      <WorldHeader world={world} onBack={onBack} />
      {lessons.error && <ErrorAlert title={say('Could not load this world')} error={lessons.error} onRetry={lessons.retry} />}
      {!lessons.ready && !lessons.error && <Skeleton className="h-40 w-full" />}
      {lessons.ready && (
        <div className="grow-world-body">
          <ol className="grow-stages">
            {lessons.stages.map((count, i) => {
              const state = i < lessons.stage.stage || (i === lessons.stage.stage && lessons.stage.done)
                ? 'done' : i === lessons.stage.stage ? 'now' : 'ahead'
              return (
                <li key={count} className="grow-stage-row" data-s={state}>
                  <span className="grow-stage-dot" aria-hidden="true">{state === 'done' ? '✓' : i + 1}</span>
                  <span className="grow-stage-text">
                    <b>{say('Stage {n}', { n: i + 1 })}</b>
                    <span>
                      {state === 'now'
                        ? say('{into} of {need} {unit} learnt', { ...lessons.stage, unit: world.unit })
                        : say('{count} {unit} learnt in all', { count, unit: world.unit })}
                    </span>
                  </span>
                  {state === 'now' && (
                    <span className="grow-lesson-bar" aria-hidden="true">
                      <i style={{ width: `${(100 * lessons.stage.into) / lessons.stage.need}%` }} />
                    </span>
                  )}
                </li>
              )
            })}
          </ol>
          <p className="grow-hint tabular-nums">
            {say('{learnt} learnt · {due} due for review · {fresh} not met yet', { learnt: lessons.learnt, due: lessons.dueCount, fresh: lessons.fresh })}
          </p>
          <p className="grow-hint">{say('Learnt means right again on another day.')}</p>
          <PrimaryButton accent={accent} disabled={!lessons.fresh && !lessons.dueCount} onClick={onStart}>
            {say('Start a lesson')}
          </PrimaryButton>
        </div>
      )}
    </div>
  )
}
