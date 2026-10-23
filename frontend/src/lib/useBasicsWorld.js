/** The Basics world: a beginner's first words with and without ال (public/grow/basics.json), record under module 'basics'. */
import { useLessonWorld } from './useLessonWorld'
import { useRememberedFlag } from './useRemembered'
import { MODULE, basicsCards, keyOfBasic } from './alifLam'

export const SOURCE_URL = '/grow/basics.json'

async function load() {
  const response = await fetch(SOURCE_URL)
  if (!response.ok) throw new Error(`Could not load the basics (${response.status})`)
  const { words } = await response.json()
  return { order: words, all: words }
}

// Whether the Basics have begun is kept on the device, not read from the record: every guest shares one record, and
// another guest's answers must neither skip this one's opening card nor move their Today on to the Basics.
const BEGUN = 'basics-begun'

export function useBasicsWorld(world) {
  const [begunHere, setBegunHere] = useRememberedFlag(BEGUN, false)
  // The first lesson on this device opens on what ال is.
  const cards = (picked, all, random) => basicsCards(picked, random, !begunHere)
  const state = useLessonWorld({ world, module: MODULE, load, keyOf: keyOfBasic, cards })
  // GrowPanel calls `began` once a Basics lesson is on screen.
  return { ...state, begunHere, began: () => setBegunHere(true) }
}
