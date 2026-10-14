/**
 * Grow, نَبَات (3:37): a little every day, in every part of the app.
 * Three screens: home, a world (SCREENS by its `kind` in worlds.json), a lesson.
 * Adding a world = a worlds.json entry + a screen here.
 */
import { useState } from 'react'

import config from '../worlds.json'
import { colorFor } from '../theme'
import { getProfile } from '../lib/profile'
import { usePrayerRecord } from '../lib/usePrayerRecord'
import { useRewards } from '../lib/useRewards'
import { useWordsWorld } from '../lib/useWordsWorld'
import GrowHome from './grow/GrowHome'
import LessonRunner from './grow/LessonRunner'
import PrayerWorld from './grow/PrayerWorld'
import WordsWorld from './grow/WordsWorld'

const WORLDS = config.worlds.map((world) => ({ ...world, accent: colorFor('world', world.id) }))
const worldOf = (id) => WORLDS.find((world) => world.id === id)

const SCREENS = {
  words: ({ world, words, back, startWords }) => (
    <WordsWorld world={world} accent={world.accent} words={words} onBack={back} onStart={startWords} />
  ),
  prayer: ({ world, prayer, back, onGo }) => (
    <PrayerWorld world={world} accent={world.accent} prayer={prayer} onBack={back} onGo={onGo} />
  ),
}

export default function GrowPanel({ onGo }) {
  const [name] = useState(getProfile)
  const { rewards } = useRewards(name)
  const words = useWordsWorld()
  const prayer = usePrayerRecord()
  // { at: 'home' } | { at: 'world', id } | { at: 'lesson', cards, back }
  const [view, setView] = useState({ at: 'home' })

  const home = () => setView({ at: 'home' })
  const open = (id) => setView({ at: 'world', id })
  const startWords = () => setView({ at: 'lesson', cards: words.makeLesson(), back: view })
  const finished = () => {
    words.refresh()
    setView(view.back ?? { at: 'home' })
  }

  let screen
  if (view.at === 'lesson') {
    screen = (
      <LessonRunner cards={view.cards} module={words.module} accent={worldOf('words').accent} rewards={rewards}
        onLeave={finished} />
    )
  } else if (view.at === 'world') {
    const world = worldOf(view.id)
    screen = SCREENS[world.kind]({ world, words, prayer, back: home, startWords, onGo })
  } else {
    screen = <GrowHome worlds={WORLDS} rewards={rewards} words={words} prayer={prayer} onOpen={open} onToday={startWords} />
  }
  return <div className="panel">{screen}</div>
}
