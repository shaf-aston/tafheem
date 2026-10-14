/**
 * Grow, نَبَات (3:37): a little every day, in every part of the app.
 * Three screens: home, a world (SCREENS by its `kind` in worlds.json), a lesson; each has an address (lib/growPlace.js),
 * written through `onVisit` and followed on back/forward through `arrival`.
 * Adding a lessons world = a worlds.json entry + a hook in `lessons` (a config of lib/useLessonWorld.js).
 */
import { useEffect, useEffectEvent, useState } from 'react'

import config from '../worlds.json'
import { colorFor } from '../theme'
import { placeOf, valueOf } from '../lib/growPlace'
import { goBack } from '../lib/journey'
import { getProfile } from '../lib/profile'
import { useHadithWorld } from '../lib/useHadithWorld'
import { useArrival } from '../lib/useArrival'
import { usePrayerRecord } from '../lib/usePrayerRecord'
import { useQuranWorld } from '../lib/useQuranWorld'
import { useRewards } from '../lib/useRewards'
import { useWordsWorld } from '../lib/useWordsWorld'
import GrowHome from './grow/GrowHome'
import LessonRunner from './grow/LessonRunner'
import LessonWorld from './grow/LessonWorld'
import PrayerWorld from './grow/PrayerWorld'

const WORLDS = config.worlds.map((world) => ({ ...world, accent: colorFor('world', world.id) }))
const worldOf = (id) => WORLDS.find((world) => world.id === id)
const WORLD_IDS = WORLDS.filter((world) => world.live).map((world) => world.id)

const SCREENS = {
  lessons: ({ world, lessons, back, start }) => (
    <LessonWorld world={world} accent={world.accent} state={lessons[world.id]} onBack={back} onStart={() => start(world.id)} />
  ),
  prayer: ({ world, prayer, back, onGo }) => (
    <PrayerWorld world={world} accent={world.accent} prayer={prayer} onBack={back} onGo={onGo} />
  ),
}

export default function GrowPanel({ incoming, arrival, onVisit, onGo }) {
  const [name] = useState(getProfile)
  const { rewards } = useRewards(name)
  const lessons = { words: useWordsWorld(worldOf('words')), hadith: useHadithWorld(worldOf('hadith')), quran: useQuranWorld(worldOf('quran')) }
  const prayer = usePrayerRecord()
  const placeAt = (value) => placeOf(value, WORLD_IDS, Object.keys(lessons))
  // { at: 'home' } | { at: 'world', id } | { at: 'lesson', id, cards?, inApp? }; a lesson without cards deals them once its world is ready.
  const [view, setView] = useState(() => placeAt(incoming))
  if (useArrival(arrival).arrived) setView(placeAt(incoming))
  if (view.at === 'lesson' && !view.cards && lessons[view.id].ready) setView({ ...view, cards: lessons[view.id].makeLesson() })

  // Leaving a lesson by any way (Continue, ×, the back arrow): its answers are saved, so re-read that world's record.
  const lessonId = view.at === 'lesson' ? view.id : null
  const refreshWorld = useEffectEvent((id) => lessons[id].refresh())
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
  // Back to where the lesson was started from; a lesson opened by its address has nowhere to go back to, so its world.
  const finished = () => {
    if (view.inApp) goBack()
    else open(view.id)
  }

  let screen
  if (view.at === 'lesson' && view.cards) {
    screen = <LessonRunner cards={view.cards} accent={worldOf(view.id).accent} rewards={rewards} onLeave={finished} />
  } else if (view.at !== 'home') {
    const world = worldOf(view.id)
    screen = SCREENS[world.kind]({ world, lessons, prayer, back: home, start, onGo })
  } else {
    screen = <GrowHome worlds={WORLDS} rewards={rewards} lessons={lessons} prayer={prayer} onOpen={open} onStart={start} />
  }
  return <div className="panel">{screen}</div>
}
