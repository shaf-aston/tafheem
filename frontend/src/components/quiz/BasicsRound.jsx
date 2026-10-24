/**
 * The Quiz's Basics set: Grow's own Basics lessons, one after another. The same cards (components/grow/exercises),
 * the same runner and the same record (module 'basics'), so a beginner meets one way of being asked whichever tab
 * they are on, and an answer here moves the Basics world on as one there does. A round is Grow's lesson session
 * (lib/grow/useLessonSession.js): dealt once the record has caught up with the last one, so its new items really are new.
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
import ErrorAlert from '../ui/ErrorAlert'
import { Skeleton } from '../ui/Skeleton'

const BASICS = { ...config.worlds.find((world) => world.id === 'basics'), accent: colorFor('world', 'basics') }

export default function BasicsRound({ say }) {
  const [name] = useState(getProfile)
  const { rewards } = useRewards(name)
  const basics = useBasicsWorld(BASICS)
  const [round, setRound] = useState(0)
  const cards = useLessonSession(() => basics, { world: BASICS.id, key: round }, (world) => world.makeLesson())

  if (basics.error) {
    return <ErrorAlert title={say('Could not load the basics')} error={basics.error} onRetry={basics.retry} />
  }
  if (!cards) return <Skeleton className="h-64 w-full" />
  if (!cards.length) return <EmptyState>{say('Every Basics step learnt and nothing due. Try the Qur’anic words next.')}</EmptyState>
  return <LessonRunner key={round} cards={cards} accent={BASICS.accent} rewards={rewards} onLeave={() => setRound(round + 1)} />
}
