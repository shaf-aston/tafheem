/**
 * A book world (Fiqh): first its parts (Purity, Prayer…), then a part's lessons, one tap from each other.
 * Above the parts, the next lesson and any review due. `state` from lib/useBookWorld.js; a lesson plays in LessonRunner.
 */
import { REVIEW } from '../../lib/useBookWorld'
import { sayIn } from '../../lib/say'
import ArabicText from '../ui/ArabicText'
import ErrorAlert from '../ui/ErrorAlert'
import PrimaryButton from '../ui/PrimaryButton'
import { Skeleton } from '../ui/Skeleton'
import Backdrop from './Backdrop'
import WorldHeader from './WorldHeader'

const say = sayIn('en')

const STATUS = {
  new: say('Not started'),
  started: say('Started'),
  done: say('Done'),
  learnt: say('Learnt'),
}

/** The next lesson to take and the review, side by side. */
function Next({ book, accent, onStart }) {
  return (
    <div className="grow-book-next">
      {book.next ? (
        <PrimaryButton accent={accent} onClick={() => onStart(book.next.id, book.next.part)}>
          {say('Next: {title}', { title: book.next.title })}
        </PrimaryButton>
      ) : <p className="grow-hint">{say('Every lesson so far is done. More are on the way.')}</p>}
      {book.due.length > 0 && (
        <button type="button" className="grow-book-review" onClick={() => onStart(REVIEW)}>
          {say('Review {n} due', { n: Math.min(book.due.length, 8) })}
        </button>
      )}
    </div>
  )
}

function Parts({ book, onPart }) {
  return (
    <div className="grow-worlds">
      {book.parts.map((part) => {
        const open = part.lessons.length > 0
        return (
          <button key={part.id} type="button" className="grow-world-tile" disabled={!open} onClick={() => onPart(part.id)}>
            <ArabicText size="lg" className="grow-tile-ar">{part.arabic}</ArabicText>
            <span className="grow-tile-name">{part.title}</span>
            <span className="grow-tile-status tabular-nums">
              {open ? say('{done} of {total} lessons', { done: part.finished, total: part.lessons.length }) : say('Coming soon')}
            </span>
            <span className="grow-lesson-bar" aria-hidden="true">
              <i style={{ width: `${open ? (100 * part.finished) / part.lessons.length : 0}%` }} />
            </span>
          </button>
        )
      })}
    </div>
  )
}

function Lessons({ part, onStart }) {
  return (
    <ol className="grow-book-lessons">
      {part.lessons.map((lesson, i) => (
        <li key={lesson.id}>
          <button type="button" className="grow-stage-row grow-book-lesson" data-s={lesson.status} onClick={() => onStart(lesson.id, part.id)}>
            <span className="grow-stage-dot" aria-hidden="true">{lesson.status === 'done' || lesson.status === 'learnt' ? '✓' : i + 1}</span>
            <span className="grow-stage-text">
              <b>{lesson.title}</b>
              <ArabicText size="sm">{lesson.arabic}</ArabicText>
            </span>
            <span className="grow-book-status">{STATUS[lesson.status]}</span>
          </button>
        </li>
      ))}
    </ol>
  )
}

export default function BookWorld({ world, accent, state: book, part: partId, onBack, onPart, onStart }) {
  const part = book.parts.find((one) => one.id === partId && one.lessons.length)
  const loading = !book.ready && !book.error
  return (
    <div className="grow-world" style={{ '--w': accent }}>
      <Backdrop id={world.backdrop} />
      {part
        ? <WorldHeader world={{ scene: part.kitab, name: part.title, arabic: part.arabic, idea: world.name }} back={world.name} onBack={() => onPart(null)} />
        : <WorldHeader world={world} onBack={onBack} />}
      {book.error && <ErrorAlert title={say('Could not load this world')} error={book.error} onRetry={book.retry} />}
      {loading && <Skeleton className="h-80 w-full" />}
      {book.ready && (
        <div className="grow-book">
          <Next book={book} accent={accent} onStart={onStart} />
          {part ? <Lessons part={part} onStart={onStart} /> : <Parts book={book} onPart={onPart} />}
          <p className="grow-hint">{say('{book} ({madhhab}). Arabic is the book’s own words; the English is ours. Learn it with a teacher too.', { book: book.book.book, madhhab: book.book.madhhab })}</p>
        </div>
      )}
    </div>
  )
}
