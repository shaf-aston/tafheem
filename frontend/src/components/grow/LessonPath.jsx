/**
 * A part's lessons as a winding path of eight-point stars, each with its title beside it: done ones gold, the next one
 * in the world's colour with a "Start" bubble over it, the rest waiting. Nothing is locked; the path only shows the way.
 * The curve is a repeating sway of steps (--x), so a long part keeps winding. Styles: .grow-path, styles/growWorlds.css.
 */
import { sayIn } from '../../lib/say'
import ArabicText from '../ui/ArabicText'

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

export default function LessonPath({ part, onStart }) {
  const next = part.lessons.findIndex((lesson) => !isDone(lesson))
  return (
    <ol className="grow-path">
      {part.lessons.map((lesson, i) => {
        const state = isDone(lesson) ? 'done' : i === next ? 'now' : 'ahead'
        return (
          <li key={lesson.id} className="rise-in" style={{ '--x': SWAY[i % SWAY.length], '--i': Math.min(i, 8) }}>
            <button type="button" className="grow-path-row" data-s={state} aria-label={`${lesson.title}, ${STATUS[lesson.status]}`}
              onClick={() => onStart(lesson.id, part.id)}>
              <span className="grow-path-star" aria-hidden="true">
                {state === 'now' && <span className="grow-path-bubble">{lesson.status === 'started' ? say('Continue') : say('Start')}</span>}
                <span className="grow-path-mark">{state === 'done' ? '✓' : i + 1}</span>
              </span>
              <span className="grow-path-label">
                <b>{lesson.title}</b>
                <ArabicText size="sm">{lesson.arabic}</ArabicText>
              </span>
            </button>
          </li>
        )
      })}
    </ol>
  )
}
