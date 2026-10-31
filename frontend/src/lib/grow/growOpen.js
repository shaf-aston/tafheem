/**
 * Grow's opening data, fetched ahead (lib/nav/tabs.js `open`: at boot when Grow is the first tab, else on idle and hover):
 * every live world's items and record, and the learner's XP. The same queries the hooks read, so Grow renders from the
 * cache instead of asking for its data only once its code has arrived (code, then data: ~300ms later on a cold load).
 */
import { getProfile } from '../learner/profile'
import { fetchRewards } from '../learner/progress'
import { summaryQuery } from '../learner/record'
import { WORLDS } from './worlds'
import { sourceQuery } from './useLessonWorld'
import { bookSourceQuery } from './useBookWorld'
import { load as basics } from './useBasicsWorld'
import { load as hadith } from './useHadithWorld'
import { load as prayer } from './usePrayerWorld'
import { loadWords } from './useWordsWorld'
import { loadQuran } from '../quran/useQuranWorld'

const LOADERS = { basics: () => basics, hadith: () => hadith, prayer: () => prayer, words: loadWords, quran: loadQuran }

const queriesOf = (world) => {
  const source = world.kind === 'book' ? bookSourceQuery(world) : LOADERS[world.id] && sourceQuery(world, LOADERS[world.id](world))
  return [source, world.module && summaryQuery(world.module)].filter(Boolean)
}

export function growOpen(client) {
  const queries = WORLDS.filter((world) => world.live).flatMap(queriesOf)
  queries.push({ queryKey: ['rewards', getProfile()], queryFn: fetchRewards, retry: false })
  // A failed one is fetched again by its hook on opening; prefetchQuery never throws.
  return Promise.all(queries.map((query) => client.prefetchQuery(query)))
}
