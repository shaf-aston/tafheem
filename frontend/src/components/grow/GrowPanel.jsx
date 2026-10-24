/**
 * Grow, نَبَات (3:37): a little every day, in every part of the app.
 * Three screens: home, a world (SCREENS by its `kind` in worlds.json), a lesson; each has an address (lib/growPlace.js),
 * written through `onVisit` and followed on back/forward through `arrival`.
 * Adding a lessons world = a worlds.json entry + a hook in `lessons` (a config of lib/grow/useLessonWorld.js);
 * a book world = an entry of kind `book`, nothing more (its data: lib/grow/useBookWorld.js): parts, then lessons, each one address deeper.
 */
import { useEffect, useEffectEvent, useState } from 'react'

import config from '../../config/worlds.json'
import { colorFor } from '../../theme'
import { nextAfter } from '../../lib/grow/bookLesson'
import { landingOf, placeOf, valueOf } from '../../lib/grow/growPlace'
import { goBack } from '../../lib/nav/journey'
import { getProfile } from '../../lib/learner/profile'
import { useHadithWorld } from '../../lib/grow/useHadithWorld'
import { useArrival } from '../../lib/nav/useArrival'
import { useBasicsWorld } from '../../lib/grow/useBasicsWorld'
import { LAST_BOOK, REVIEW, useBookWorlds } from '../../lib/grow/useBookWorld'
import { useQuranWorld } from '../../lib/quran/useQuranWorld'
import { useRemembered } from '../../lib/store/useRemembered'
import { useRewards } from '../../lib/learner/useRewards'
import { useWordsWorld } from '../../lib/grow/useWordsWorld'
import BookWorld from './BookWorld'
import GrowHome from './GrowHome'
import LessonRunner from './LessonRunner'
import LessonWorld from './LessonWorld'

const WORLDS = config.worlds.map((world) => ({ ...world, accent: colorFor('world', world.id) }))
const worldOf = (id) => WORLDS.find((world) => world.id === id)
const WORLD_IDS = WORLDS.filter((world) => world.live).map((world) => world.id)
const BOOKS = WORLDS.filter((world) => world.kind === 'book')
const BOOK_IDS = BOOKS.map((world) => world.id)

const SCREENS = {
  lessons: ({ world, lessons, back, start }) => (
    <LessonWorld world={world} accent={world.accent} state={lessons[world.id]} onBack={back} onStart={() => start(world.id)} />
  ),
  book: ({ world, books, view, back, go, startBook }) => (
    <BookWorld world={world} accent={world.accent} state={books[world.id]} place={view.part} onBack={back}
      onPart={(part) => go(part ? { at: 'world', id: world.id, part } : { at: 'world', id: world.id })}
      onStart={(lesson, part) => startBook(world.id, lesson, part)} />
  ),
}

export default function GrowPanel({ incoming, arrival, handed = false, onVisit }) {
  const [name] = useState(getProfile)
  const { rewards } = useRewards(name)
  const lessons = {
    basics: useBasicsWorld(worldOf('basics')),
    words: useWordsWorld(worldOf('words')),
    hadith: useHadithWorld(worldOf('hadith')),
    quran: useQuranWorld(worldOf('quran')),
  }
  const placeAt = (value) => placeOf(value, WORLD_IDS, Object.keys(lessons), BOOK_IDS)
  // { at: 'home' } | { at: 'world', id, part? } | { at: 'lesson', id, part?, lesson?, cards?, inApp? }; a lesson without cards deals them once its world is ready.
  // Grow opening on a lesson's saved address (a reload, the tab reopened) lands on home with that lesson offered (landingOf);
  // its answers are kept either way. A lesson handed in by a tap elsewhere (Home's "Start the basics") starts at once.
  const [landed] = useState(() => (handed ? { view: placeAt(incoming), resume: null } : landingOf(placeAt(incoming))))
  const [view, setView] = useState(landed.view)
  const [resume, setResume] = useState(landed.resume)
  if (useArrival(arrival).arrived) {
    setView(placeAt(incoming))
    setResume(null)
  }
  // A book world fetches the part files the view needs (its open part, the lesson's, a review's).
  const books = useBookWorlds(BOOKS, view)
  const sourceOf = (id) => books[id] ?? lessons[id]
  // A lesson's cards: a book world's by the lesson's id, once its part is in; any other world's next lesson.
  const deal = (at) => (books[at.id] ? books[at.id].makeLesson(at.lesson) : lessons[at.id].makeLesson())
  const dealable = (id) => (books[id] ? books[id].dealable : lessons[id].ready)
  if (view.at === 'lesson' && !view.cards && dealable(view.id)) {
    const cards = deal(view)
    // A lesson the book does not have, or a review with nothing due: that world's page instead.
    setView(cards?.length ? { ...view, cards } : { at: 'world', id: view.id, ...(view.part && { part: view.part }) })
  }

  // Leaving a lesson by any way (Continue, ×, the back arrow, on to the next lesson): its answers are saved, so re-read
  // that world's record.
  const playing = view.at === 'lesson' ? `${view.id}/${view.lesson ?? ''}` : null
  const refreshWorld = useEffectEvent((id) => sourceOf(id).refresh())
  // And a world that keeps "begun" on the device (the Basics) is told once its lesson is on screen.
  const beginWorld = useEffectEvent((id) => sourceOf(id).began?.())
  const dealt = Boolean(view.cards)
  useEffect(() => {
    if (!playing || !dealt) return
    const id = playing.split('/')[0]
    beginWorld(id)
    return () => refreshWorld(id)
  }, [playing, dealt])

  const [, rememberBook] = useRemembered(LAST_BOOK, BOOK_IDS, '')
  const go = (next) => {
    setResume(null)
    if (next.at === 'lesson' && BOOK_IDS.includes(next.id)) rememberBook(next.id)
    setView(next)
    onVisit?.(valueOf(next))
  }
  const home = () => go({ at: 'home' })
  const open = (id) => go({ at: 'world', id })
  const start = (id) => go({ at: 'lesson', id, cards: lessons[id].makeLesson(), inApp: true })
  // Dealt once the lesson's part is in (above); a part already open has it at once.
  const startBook = (id, lesson, part) => go({ at: 'lesson', id, lesson, ...(part && { part }), inApp: true })
  // Back to where the lesson was started from; a lesson opened by its address has nowhere to go back to, so its world (a book's part).
  const finished = () => {
    if (view.inApp) goBack()
    else go({ at: 'world', id: view.id, ...(view.part && { part: view.part }) })
  }

  // A book lesson's end offers the next open lesson after it, named with its part when that is another; a review's end
  // does not. That lesson ends on its part's path.
  const nextOf = () => {
    const book = books[view.id]
    const after = book && view.lesson !== REVIEW && nextAfter(book.parts, view.lesson)
    if (!after) return null
    const part = after.part !== view.part && book.parts.find((one) => one.id === after.part)
    return { title: part ? `${part.title}: ${after.title}` : after.title, go: () => go({ at: 'lesson', id: view.id, lesson: after.id, part: after.part }) }
  }

  let screen
  if (view.at === 'lesson' && view.cards) {
    screen = (
      <LessonRunner key={playing} cards={view.cards} accent={worldOf(view.id).accent} rewards={rewards} next={nextOf()} onLeave={finished} />
    )
  } else if (view.at !== 'home') {
    const world = worldOf(view.id)
    screen = SCREENS[world.kind]({ world, lessons, books, view, back: home, go, start, startBook })
  } else {
    screen = (
      <GrowHome worlds={WORLDS} rewards={rewards} lessons={lessons} books={books} resume={resume} onResume={() => go(resume)}
        onOpen={open} onStart={start} onStartBook={startBook} />
    )
  }
  return <div className="panel">{screen}</div>
}
