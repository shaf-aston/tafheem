/**
 * A lessons world (Words, Hadith, Quran): its picture if worlds.json gives it a `view` (./scenes), else a row per stage;
 * beside it on a wide screen (first on a phone) the stage by items learnt (the server's "known") and the lesson button,
 * held in view. `state` from lib/useLessonWorld.js.
 */
import { sayIn } from '../../lib/say'
import ErrorAlert from '../ui/ErrorAlert'
import PrimaryButton from '../ui/PrimaryButton'
import { Skeleton } from '../ui/Skeleton'
import { SCENES } from './scenes'
import WorldHeader from './WorldHeader'

const say = sayIn('en')

/** Every stage as a row; the current one with its bar. */
function Stages({ world, lessons }) {
  return (
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
            {state === 'now' && <Bar stage={lessons.stage} />}
          </li>
        )
      })}
    </ol>
  )
}

const Bar = ({ stage }) => (
  <span className="grow-lesson-bar" aria-hidden="true"><i style={{ width: `${(100 * stage.into) / stage.need}%` }} /></span>
)

/** The current stage alone, under a scene. */
function StageLine({ world, lessons }) {
  return (
    <div className="grow-stage-line">
      <p className="tabular-nums">
        {say('Stage {n} of {total} · {into} of {need} {unit} learnt', { n: lessons.stage.stage + 1, total: lessons.stages.length, ...lessons.stage, unit: world.unit })}
      </p>
      <Bar stage={lessons.stage} />
    </div>
  )
}

export default function LessonWorld({ world, accent, state: lessons, onBack, onStart }) {
  const Scene = SCENES[world.view]
  return (
    <div style={{ '--w': accent }}>
      <WorldHeader world={world} onBack={onBack} />
      {lessons.error && <ErrorAlert title={say('Could not load this world')} error={lessons.error} onRetry={lessons.retry} />}
      {/* About the picture's height, so the page does not jump when it lands. */}
      {!lessons.ready && !lessons.error && <Skeleton className={Scene ? 'h-[32rem] w-full' : 'h-80 w-full'} />}
      {lessons.ready && (
        <div className="grow-world-body">
          <div className="grow-world-main">
            {Scene ? <Scene items={lessons.items} world={world} /> : <Stages world={world} lessons={lessons} />}
          </div>
          <aside className="grow-world-side" aria-label={say('Your progress')}>
            {Scene && <StageLine world={world} lessons={lessons} />}
            <p className="grow-hint tabular-nums">
              {say('{learnt} learnt · {due} due for review · {fresh} not met yet', { learnt: lessons.learnt, due: lessons.dueCount, fresh: lessons.fresh })}
            </p>
            <PrimaryButton accent={accent} disabled={!lessons.fresh && !lessons.dueCount} onClick={onStart}>
              {say('Start a lesson')}
            </PrimaryButton>
            <p className="grow-hint">{say('Learnt means right again on another day.')}</p>
          </aside>
        </div>
      )}
    </div>
  )
}
