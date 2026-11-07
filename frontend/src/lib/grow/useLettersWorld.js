/** The Letters world: the 28 letters by shape (public/grow/letters.json); recorded under module 'letters'. */
import { fetchStatic } from '../api/staticQuery'
import { useLessonWorld } from './useLessonWorld'
import { keyOfLetter, lettersCards } from './lettersLesson'

export const SOURCE_URL = '/grow/letters.json'

export async function load() {
  const { letters } = await fetchStatic(SOURCE_URL, 'the letters')
  return { order: letters, all: letters }
}

export function useLettersWorld(world) {
  return useLessonWorld({ world, load, keyOf: keyOfLetter, cards: lettersCards })
}
