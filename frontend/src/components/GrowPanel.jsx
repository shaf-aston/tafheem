/**
 * Grow, نَبَات (3:37): a little every day, in every part of the app.
 * Three screens: home, a world (SCREENS by its `kind` in worlds.json), a lesson.
 * Adding a lessons world = a worlds.json entry + a hook in LESSONS (a config of lib/useLessonWorld.js).
 */
import { useState } from 'react'

import config from '../worlds.json'
import { colorFor } from '../theme'
import { getProfile } from '../lib/profile'
import { useHadithWorld } from '../lib/useHadithWorld'
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

const SCREENS = {
  lessons: ({ world, lessons, back, start }) => (
    <LessonWorld world={world} accent={world.accent} state={lessons[world.id]} onBack={back} onStart={() => start(world.id)} />
  ),
  prayer: ({ world, prayer, back, onGo }) => (
    <PrayerWorld world={world} accent={world.accent} prayer={prayer} onBack={back} onGo={onGo} />
  ),
}

export default function GrowPanel({ onGo }) {
  const [name] = useState(getProfile)
  const { rewards } = useRewards(name)
  const lessons = {
    words: useWordsWorld(worldOf('words')),
    quran: useQuranWorld(worldOf('quran')),
    hadith: useHadithWorld(worldOf('hadith')),
  }
  const prayer = usePrayerRecord()
  // { at: 'home' } | { at: 'world', id } | { at: 'lesson', id, cards, back }
  const [view, setView] = useState({ at: 'home' })

  const home = () => setView({ at: 'home' })
  const open = (id) => setView({ at: 'world', id })
  const start = (id) => setView({ at: 'lesson', id, cards: lessons[id].makeLesson(), back: view })
  const finished = () => {
    lessons[view.id].refresh()
    setView(view.back ?? { at: 'home' })
  }

  let screen
  if (view.at === 'lesson') {
    screen = <LessonRunner cards={view.cards} accent={worldOf(view.id).accent} rewards={rewards} onLeave={finished} />
  } else if (view.at === 'world') {
    const world = worldOf(view.id)
    screen = SCREENS[world.kind]({ world, lessons, prayer, back: home, start, onGo })
  } else {
    screen = <GrowHome worlds={WORLDS} rewards={rewards} lessons={lessons} prayer={prayer} onOpen={open} onStart={start} />
  }
  return <div className="panel">{screen}</div>
}
