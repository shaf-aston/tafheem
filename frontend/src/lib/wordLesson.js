/**
 * Words world cards: a teach card, then the quiz's own question (buildQuestion), filed under the
 * quiz's module and meaningKey so Grow and the Quiz tab share one record.
 */
import { buildQuestion } from './quiz'
import { MODULE } from './quizBanks'
import { weave } from './lesson'

export const keyOfWord = (word) => word.meaningKey

/** Wrong options come from the answer's own topic and type when enough of those exist (more than a question needs), else from `all`. */
export function optionPool(word, all, need = 5) {
  const shared = new Set(word.groups ?? [])
  const near = shared.size ? all.filter((other) => other.wordType === word.wordType && (other.groups ?? []).some((group) => shared.has(group))) : []
  return near.length > need ? near : all
}

/** `picked` from lessonItems; `all` supplies wrong options. */
export function wordCards(picked, all, random = Math.random) {
  return weave(picked, {
    teach: (word) => ({ kind: 'teach', id: `teach:${word.meaningKey}`, ar: word.ar, en: word.en, tag: 'New word' }),
    asks: (word, isNew) => {
      const question = buildQuestion([word], { distractorBank: optionPool(word, all), random })
      return [{
        kind: 'meaning',
        id: `ask:${word.meaningKey}`,
        tag: isNew ? 'New word' : 'Review',
        question,
        answerText: question.answerText,
        record: { module: MODULE, item: word.meaningKey, context: { bank: 'grow', world: 'words', word: word.ar } },
      }]
    },
  })
}
