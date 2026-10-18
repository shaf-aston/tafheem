/**
 * A book world (Fiqh), one level at a time: its areas (Worship, Trade…), an area's parts (Purity, Prayer…), a part's lessons.
 * A book without areas opens on its parts. Above them, the next lesson and any review due. `place` is the address step,
 * an area's id or a part's. `state` from lib/useBookWorld.js; a lesson plays in LessonRunner.
 */
import { areaOf } from '../../lib/bookLesson'
import { REVIEW } from '../../lib/useBookWorld'
import { sayIn } from '../../lib/say'
import ArabicText from '../ui/ArabicText'
import ErrorAlert from '../ui/ErrorAlert'
import PrimaryButton from '../ui/PrimaryButton'
import { Skeleton } from '../ui/Skeleton'
import Backdrop from './Backdrop'
import LessonPath from './LessonPath'
import WorldHeader from './WorldHeader'

const say = sayIn('en')

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

/** A tile per area or part: its name, lessons finished of those it has; one with none yet shows as coming. */
function Tiles({ items, onOpen }) {
  return (
    <div className="grow-worlds">
      {items.map((item) => {
        const total = item.total ?? item.lessons.length
        return (
          <button key={item.id} type="button" className="grow-world-tile" data-look={item.look} disabled={!total} onClick={() => onOpen(item.id)}>
            <ArabicText size="lg" className="grow-tile-ar">{item.arabic}</ArabicText>
            <span className="grow-tile-name">{item.title}</span>
            <span className="grow-tile-status tabular-nums">
              {total ? say('{done} of {total} lessons', { done: item.finished, total }) : say('Coming soon')}
            </span>
            <span className="grow-lesson-bar" aria-hidden="true">
              <i style={{ width: `${total ? (100 * item.finished) / total : 0}%` }} />
            </span>
          </button>
        )
      })}
    </div>
  )
}

/** The header for where the reader is: the world, an area (back to the world), or a part (back to its area, if any). */
function Header({ world, area, part, onBack, onPart }) {
  if (part) {
    const up = area?.title ?? world.name
    return (
      <WorldHeader world={{ scene: part.kitab, name: part.title, arabic: part.arabic, idea: up }} back={up}
        onBack={() => onPart(area?.id ?? null)} />
    )
  }
  if (area) {
    return <WorldHeader world={{ scene: world.name, name: area.title, arabic: area.arabic, idea: area.idea }} back={world.name} onBack={() => onPart(null)} />
  }
  return <WorldHeader world={world} onBack={onBack} />
}

export default function BookWorld({ world, accent, state: book, place, onBack, onPart, onStart }) {
  const part = book.parts.find((one) => one.id === place && one.lessons.length)
  const area = part ? areaOf(book.areas, part.id) : book.areas.find((one) => one.id === place && one.total)
  const loading = !book.ready && !book.error
  let body
  if (part) body = <LessonPath part={part} onStart={onStart} />
  else if (area) body = <Tiles items={area.parts} onOpen={onPart} />
  else body = <Tiles items={book.areas.length ? book.areas : book.parts} onOpen={onPart} />
  return (
    <div className="grow-world" style={{ '--w': accent }}>
      <Backdrop id={world.backdrop} />
      <div data-look={(part ?? area)?.look}>
        <Header world={world} area={area} part={part} onBack={onBack} onPart={onPart} />
      </div>
      {book.error && <ErrorAlert title={say('Could not load this world')} error={book.error} onRetry={book.retry} />}
      {loading && <Skeleton className="h-80 w-full" />}
      {book.ready && (
        <div className="grow-book">
          {book.offline && <p className="grow-hint">{say('Your progress could not be loaded, so it is not shown. The lessons still work.')}</p>}
          <Next book={book} accent={accent} onStart={onStart} />
          {body}
          <p className="grow-hint">{say('{book} ({madhhab}). Arabic is the book’s own words; the English is ours. Learn it with a teacher too.', { book: book.book.book, madhhab: book.book.madhhab })}</p>
        </div>
      )}
    </div>
  )
}
