/** The Basics world: a beginner's first words with and without ال (public/grow/basics.json), record under module 'basics'. */
import { useLessonWorld } from './useLessonWorld'
import { MODULE, basicsCards, keyOfBasic } from './alifLam'

export const SOURCE_URL = '/grow/basics.json'

async function load() {
  const response = await fetch(SOURCE_URL)
  if (!response.ok) throw new Error(`Could not load the basics (${response.status})`)
  const { words } = await response.json()
  return { order: words, all: words }
}

export function useBasicsWorld(world) {
  return useLessonWorld({ world, module: MODULE, load, keyOf: keyOfBasic, cards: basicsCards })
}
