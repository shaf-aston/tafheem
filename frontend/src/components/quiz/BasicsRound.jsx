/**
 * The Quiz's Basics set: Grow's own Basics lessons, one after another. The same cards (components/grow/exercises),
 * the same runner and the same record (module 'basics'), so a beginner meets one way of being asked whichever tab
 * they are on, and an answer here moves the Basics world on as one there does. A round is dealt once the record has
 * caught up with the last one, so its new items really are new.
 */
import { useEffect, useEffectEvent, useState } from 'react'

import config from '../../worlds.json'
import { colorFor } from '../../theme'
import { getProfile } from '../../lib/profile'
import { useBasicsWorld } from '../../lib/useBasicsWorld'
import { useRewards } from '../../lib/useRewards'
import LessonRunner from '../grow/LessonRunner'
import EmptyState from '../ui/EmptyState'
import ErrorAlert from '../ui/ErrorAlert'
import { Skeleton } from '../ui/Skeleton'

const BASICS = { ...config.worlds.find((world) => world.id === 'basics'), accent: colorFor('world', 'basics') }

export default function BasicsRound({ say }) {
  const [name] = useState(getProfile)
  const { rewards } = useRewards(name)
  const basics = useBasicsWorld(BASICS)
  const [round, setRound] = useState({ at: 0, cards: null })
  if (!round.cards && basics.ready && !basics.settling) setRound({ ...round, cards: basics.makeLesson() })

  // As in Grow: a Basics lesson on screen is the Basics begun here.
  const dealt = Boolean(round.cards)
  const begin = useEffectEvent(() => basics.began())
  useEffect(() => { if (dealt) begin() }, [dealt])

  if (basics.error) {
    return <ErrorAlert title={say('Could not load the basics')} error={basics.error} onRetry={basics.retry} />
  }
  if (!round.cards) return <Skeleton className="h-64 w-full" />
  if (!round.cards.length) return <EmptyState>{say('Every Basics step learnt and nothing due. Try the Qur’anic words next.')}</EmptyState>
  const another = () => {
    basics.refresh()
    setRound({ at: round.at + 1, cards: null })
  }
  return <LessonRunner key={round.at} cards={round.cards} accent={BASICS.accent} rewards={rewards} onLeave={another} />
}
