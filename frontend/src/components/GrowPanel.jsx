/**
 * Grow, نَبَات (3:37): a little every day, in every part of the app.
 * Three screens: home, a world (SCREENS by its `kind` in worlds.json), a lesson; each has an address (lib/growPlace.js),
 * written through `onVisit` and followed on back/forward through `arrival`.
 * Adding a lessons world = a worlds.json entry + a hook in `lessons` (a config of lib/useLessonWorld.js);
 * a book world = an entry of kind `book` + its hook in `books` (lib/useBookWorld.js): parts, then lessons, each one address deeper.
 */
import { useEffect, useEffectEvent, useState } from 'react'

import config from '../worlds.json'
import { colorFor } from '../theme'
import { placeOf, valueOf } from '../lib/growPlace'
import { goBack } from '../lib/journey'
import { getProfile } from '../lib/profile'
import { useHadithWorld } from '../lib/useHadithWorld'
import { useArrival } from '../lib/useArrival'
import { useBookWorld } from '../lib/useBookWorld'
import { useQuranWorld } from '../lib/useQuranWorld'
import { useRewards } from '../lib/useRewards'
import { useWordsWorld } from '../lib/useWordsWorld'
import BookWorld from './grow/BookWorld'
import GrowHome from './grow/GrowHome'
import LessonRunner from './grow/LessonRunner'
import LessonWorld from './grow/LessonWorld'

const WORLDS = config.worlds.map((world) => ({ ...world, accent: colorFor('world', world.id) }))
const worldOf = (id) => WORLDS.find((world) => world.id === id)
const WORLD_IDS = WORLDS.filter((world) => world.live).map((world) => world.id)

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

export default function GrowPanel({ incoming, arrival, onVisit }) {
  const [name] = useState(getProfile)
  const { rewards } = useRewards(name)
  const lessons = { words: useWordsWorld(worldOf('words')), hadith: useHadithWorld(worldOf('hadith')), quran: useQuranWorld(worldOf('quran')) }
  const books = { fiqh: useBookWorld(worldOf('fiqh')), nahw: useBookWorld(worldOf('nahw')), sarf: useBookWorld(worldOf('sarf')) }
  const sourceOf = (id) => books[id] ?? lessons[id]
  const placeAt = (value) => placeOf(value, WORLD_IDS, Object.keys(lessons), Object.keys(books))
  // A lesson's cards: a book world's by the lesson's id, any other world's next lesson.
  const deal = (at) => (books[at.id] ? books[at.id].makeLesson(at.lesson) : lessons[at.id].makeLesson())
  // { at: 'home' } | { at: 'world', id, part? } | { at: 'lesson', id, part?, lesson?, cards?, inApp? }; a lesson without cards deals them once its world is ready.
  const [view, setView] = useState(() => placeAt(incoming))
  if (useArrival(arrival).arrived) setView(placeAt(incoming))
  if (view.at === 'lesson' && !view.cards && sourceOf(view.id).ready) {
    const cards = deal(view)
    // A lesson the book does not have, or a review with nothing due: that world's page instead.
    setView(cards?.length ? { ...view, cards } : { at: 'world', id: view.id, ...(view.part && { part: view.part }) })
  }

  // Leaving a lesson by any way (Continue, ×, the back arrow): its answers are saved, so re-read that world's record.
  const lessonId = view.at === 'lesson' ? view.id : null
  const refreshWorld = useEffectEvent((id) => sourceOf(id).refresh())
  useEffect(() => {
    if (lessonId) return () => refreshWorld(lessonId)
  }, [lessonId])

  const go = (next) => {
    setView(next)
    onVisit?.(valueOf(next))
  }
  const home = () => go({ at: 'home' })
  const open = (id) => go({ at: 'world', id })
  const start = (id) => go({ at: 'lesson', id, cards: lessons[id].makeLesson(), inApp: true })
  const startBook = (id, lesson, part) => go({ at: 'lesson', id, lesson, ...(part && { part }), cards: books[id].makeLesson(lesson), inApp: true })
  // Back to where the lesson was started from; a lesson opened by its address has nowhere to go back to, so its world (a book's part).
  const finished = () => {
    if (view.inApp) goBack()
    else go({ at: 'world', id: view.id, ...(view.part && { part: view.part }) })
  }

  let screen
  if (view.at === 'lesson' && view.cards) {
    screen = <LessonRunner cards={view.cards} accent={worldOf(view.id).accent} rewards={rewards} onLeave={finished} />
  } else if (view.at !== 'home') {
    const world = worldOf(view.id)
    screen = SCREENS[world.kind]({ world, lessons, books, view, back: home, go, start, startBook })
  } else {
    screen = (
      <GrowHome worlds={WORLDS} rewards={rewards} lessons={lessons} books={books} onOpen={open} onStart={start}
        onStartBook={startBook} />
    )
  }
  return <div className="panel">{screen}</div>
}
