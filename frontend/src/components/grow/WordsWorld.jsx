/**
 * The Words world: the quiz's own word set, walked through a few new words at a
 * time, with reviews mixed in. Its stages are counts of words learnt
 * (worlds.json); learnt is the server's "known", the same measure the profile
 * and the rankings use, so no number here can disagree with them.
 */
import { sayIn } from '../../lib/say'
import ErrorAlert from '../ui/ErrorAlert'
import PrimaryButton from '../ui/PrimaryButton'
import { Skeleton } from '../ui/Skeleton'
import WorldHeader from './WorldHeader'

const say = sayIn('en')

export default function WordsWorld({ world, accent, words, onBack, onStart }) {
  return (
    <div style={{ '--w': accent }}>
      <WorldHeader world={world} onBack={onBack} />
      {words.error && <ErrorAlert title={say('Could not load the words')} error={words.error} onRetry={words.retry} />}
      {!words.ready && !words.error && <Skeleton className="h-40 w-full" />}
      {words.ready && (
        <div className="grow-world-body">
          <ol className="grow-stages">
            {words.stages.map((count, i) => {
              const state = i < words.stage.stage || (i === words.stage.stage && words.stage.done)
                ? 'done' : i === words.stage.stage ? 'now' : 'ahead'
              return (
                <li key={count} className="grow-stage-row" data-s={state}>
                  <span className="grow-stage-dot" aria-hidden="true">{state === 'done' ? '✓' : i + 1}</span>
                  <span className="grow-stage-text">
                    <b>{say('Stage {n}', { n: i + 1 })}</b>
                    <span>
                      {state === 'now'
                        ? say('{into} of {need} words learnt', words.stage)
                        : say('{count} words learnt in all', { count })}
                    </span>
                  </span>
                  {state === 'now' && (
                    <span className="grow-lesson-bar" aria-hidden="true">
                      <i style={{ width: `${(100 * words.stage.into) / words.stage.need}%` }} />
                    </span>
                  )}
                </li>
              )
            })}
          </ol>
          <p className="grow-hint tabular-nums">
            {say('{learnt} learnt · {due} due for review · {fresh} not met yet', { learnt: words.learnt, due: words.dueCount, fresh: words.fresh })}
          </p>
          <p className="grow-hint">{say('A word counts as learnt once you get it right again on another day.')}</p>
          <PrimaryButton accent={accent} disabled={!words.fresh && !words.dueCount} onClick={onStart}>
            {say('Start a lesson')}
          </PrimaryButton>
        </div>
      )}
    </div>
  )
}
