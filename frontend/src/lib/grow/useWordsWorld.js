/** The Words world: the quiz's word set and the Quiz's own record (worlds.json names it, `quiz`: English). */
import { useLessonWorld } from './useLessonWorld'
import { allWords, wordsFor } from '../quiz/quizBanks'
import { keyOfWord, wordCards } from './wordLesson'

export const loadWords = (world) => async () => ({ order: await wordsFor(world.lesson.bank), all: await allWords() })

export function useWordsWorld(world) {
  return useLessonWorld({
    world,
    load: loadWords(world),
    keyOf: keyOfWord,
    cards: wordCards,
  })
}
