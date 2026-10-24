/** The Words world: the quiz's word set and the Quiz's own record (worlds.json names it, `quiz`: English). */
import { useLessonWorld } from './useLessonWorld'
import { allWords, wordsFor } from '../quiz/quizBanks'
import { keyOfWord, wordCards } from './wordLesson'

export function useWordsWorld(world) {
  return useLessonWorld({
    world,
    load: async () => ({ order: await wordsFor(world.lesson.bank), all: await allWords() }),
    keyOf: keyOfWord,
    cards: wordCards,
  })
}
