/**
 * The Basics world: a beginner's first words with and without ال (public/grow/basics.json), and between them the small
 * additions that change a word (verbs: public/grow/basics-verbs.json; the path: lib/basicsSkills.js); recorded under module 'basics'.
 */
import { useLessonWorld } from './useLessonWorld'
import { useRememberedFlag } from './useRemembered'
import { MODULE, keyOfBasic } from './alifLam'
import { basicsCards, pathItems } from './basicsSkills'

export const SOURCE_URL = '/grow/basics.json'
export const VERBS_URL = '/grow/basics-verbs.json'

async function json(url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`Could not load the basics (${response.status})`)
  return response.json()
}

// The verbs are only for the verb skills: without them (offline, before the file is saved) the words and the rest still load.
const verbsOrNone = () => json(VERBS_URL).then(({ verbs }) => verbs, () => null)

async function load() {
  const [{ words, path }, verbs] = await Promise.all([json(SOURCE_URL), verbsOrNone()])
  const items = pathItems(words, { verbs, path })
  return { order: items, all: items }
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
