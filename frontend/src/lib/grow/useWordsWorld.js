/** The Words world: the quiz's word set and the Quiz's own record (module 'quiz', English). */
import { useLessonWorld } from '../useLessonWorld'
import { MODULE, allWords, wordsFor } from '../quizBanks'
import { keyOfWord, wordCards } from '../wordLesson'

export function useWordsWorld(world) {
  return useLessonWorld({
    world,
    module: MODULE,
    load: async () => ({ order: await wordsFor(world.lesson.bank), all: await allWords() }),
    keyOf: keyOfWord,
    cards: wordCards,
    alsoRefresh: ['quiz-review', 'quiz-progress'],
  })
}
