/**
 * A part's lessons as a winding path, each node with its title beside it: done ones gold, the next one in the world's
 * colour with a "Start" bubble over it, the rest waiting. Nothing is locked; the path only shows the way. The part's
 * `look` (lib/grow/bookLesson.js LOOKS) picks the nodes: courtyard stars, or round garden nodes with a leaf sprig. The curve is
 * a repeating sway of steps (--x), so a long part keeps winding. An `extra` lesson (a rare case) is a smaller node marked
 * Extra, and the "Start" bubble passes it by until the core is done (lib/grow/bookLesson.js firstOpen). A part with `units` (the book's
 * own sections inside it) heads each unit's lessons with its name and how many are done. Styles: .grow-path, styles/growWorlds.css.
 */
import { firstOpen } from '../../lib/grow/bookLesson'
import { sayIn } from '../../lib/text/say'
import ArabicText from '../ui/text/ArabicText'

const say = sayIn('en')

// How far each lesson sits from the left edge, in steps; repeats every eight lessons.
const SWAY = [0, 1, 2, 1, 0, -1, -2, -1]

const STATUS = {
  new: say('Not started'),
  started: say('Started'),
  done: say('Done'),
  learnt: say('Learnt'),
}

const isDone = (lesson) => lesson.status === 'done' || lesson.status === 'learnt'

// The unit (if any) that starts at each lesson, by the lesson's id.
const unitStarts = (part) => new Map((part.units ?? []).map((unit) => [unit.lessons[0], unit]))

function UnitHead({ unit, lessons }) {
  const own = lessons.filter((lesson) => unit.lessons.includes(lesson.id))
  return (
    <li className="grow-path-unit">
      <h3>{unit.title}</h3>
      <ArabicText size="sm">{unit.arabic}</ArabicText>
      <span className="tabular-nums">{say('{done} of {total}', { done: own.filter(isDone).length, total: own.length })}</span>
    </li>
  )
}

export default function LessonPath({ part, onStart }) {
  const next = part.lessons.indexOf(firstOpen(part.lessons))
  const starts = unitStarts(part)
  return (
    <ol className="grow-path" data-look={part.look}>
      {part.lessons.flatMap((lesson, i) => {
        const unit = starts.get(lesson.id)
        const head = unit ? [<UnitHead key={`unit-${lesson.id}`} unit={unit} lessons={part.lessons} />] : []
        const state = isDone(lesson) ? 'done' : i === next ? 'now' : 'ahead'
        return [...head, (
          <li key={lesson.id} className="rise-in" style={{ '--x': SWAY[i % SWAY.length], '--i': Math.min(i, 8) }}>
            <button type="button" className="grow-path-row" data-s={state} data-extra={lesson.extra ? '' : undefined}
              aria-label={`${lesson.title}${lesson.extra ? `, ${say('extra')}` : ''}, ${STATUS[lesson.status]}`}
              onClick={() => onStart(lesson.id, part.id)}>
              <span className="grow-path-star" aria-hidden="true">
                {state === 'now' && <span className="grow-path-bubble">{lesson.status === 'started' ? say('Continue') : say('Start')}</span>}
                <span className="grow-path-mark">{state === 'done' ? '✓' : i + 1}</span>
                <span className="grow-path-leaf" />
              </span>
              <span className="grow-path-label">
                <b>{lesson.title}</b>
                {lesson.extra && <span className="grow-path-extra">{say('Extra')}</span>}
                <ArabicText size="sm">{lesson.arabic}</ArabicText>
              </span>
            </button>
          </li>
        )]
      })}
    </ol>
  )
}
