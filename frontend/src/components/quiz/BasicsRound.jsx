/**
 * The Quiz's Basics set: Grow's own Basics lessons, one after another. The same cards (components/grow/exercises),
 * the same runner and the same record (module 'basics'), so a beginner meets one way of being asked whichever tab
 * they are on, and an answer here moves the Basics world on as one there does. A round is Grow's lesson session
 * (lib/grow/useLessonSession.js): dealt once the record has caught up with the last one, so its new items really are new.
 * A lesson's end goes straight on to the next; its × rests until asked for another, so leaving is leaving.
 */
import { useState } from 'react'

import config from '../../config/worlds.json'
import { colorFor } from '../../theme'
import { getProfile } from '../../lib/learner/profile'
import { useBasicsWorld } from '../../lib/grow/useBasicsWorld'
import { useLessonSession } from '../../lib/grow/useLessonSession'
import { useRewards } from '../../lib/learner/useRewards'
import LessonRunner from '../grow/LessonRunner'
import EmptyState from '../ui/EmptyState'
import PrimaryButton from '../ui/PrimaryButton'
import ErrorAlert from '../ui/ErrorAlert'
import { Skeleton } from '../ui/Skeleton'

const BASICS = { ...config.worlds.find((world) => world.id === 'basics'), accent: colorFor('world', 'basics') }

export default function BasicsRound({ say }) {
  const [name] = useState(getProfile)
  const { rewards } = useRewards(name)
  const basics = useBasicsWorld(BASICS)
  const [round, setRound] = useState(0)
  const [resting, setResting] = useState(false)
  const cards = useLessonSession(() => basics, resting ? null : { world: BASICS.id, key: round }, (world) => world.makeLesson())
  const another = () => {
    setRound(round + 1)
    setResting(false)
  }

  if (basics.error) {
    return <ErrorAlert title={say('Could not load the basics')} error={basics.error} onRetry={basics.retry} />
  }
  if (resting) {
    return (
      <div className="flex flex-col items-center gap-3 py-6 text-center">
        <p className="text-[var(--text-dim)]">{say('Lesson left. Your answers are saved.')}</p>
        <PrimaryButton accent={BASICS.accent} onClick={another}>{say('Start a lesson')}</PrimaryButton>
      </div>
    )
  }
  if (!cards) return <Skeleton className="h-64 w-full" />
  if (!cards.length) return <EmptyState>{say('Every Basics step learnt and nothing due. Try the Qur’anic words next.')}</EmptyState>
  return <LessonRunner key={round} cards={cards} accent={BASICS.accent} rewards={rewards} onLeave={another} onQuit={() => setResting(true)} />
}
