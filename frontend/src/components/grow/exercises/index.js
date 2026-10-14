/**
 * Exercise kinds: one entry per kind; the lesson runner knows none by name.
 *   Card        ({ card, value, setValue, result }) => JSX
 *   ready       can Check be pressed yet
 *   check       is the value right (absent: a teach card, nothing asked)
 *   correction  what to say when wrong
 * A checked card carries `record` ({ module, item, context }), what the progress store files it under.
 */
import { sayIn } from '../../../lib/say'
import GapCard from './GapCard'
import HadithCard from './HadithCard'
import MeaningCard from './MeaningCard'
import TeachCard from './TeachCard'

const say = sayIn('en')
const picked = (value) => value != null

export const KINDS = {
  teach: { Card: TeachCard },
  hadith: { Card: HadithCard },
  meaning: {
    Card: MeaningCard,
    ready: picked,
    check: (card, value) => value === card.question.answerId,
    correction: (card) => say('Not quite. It means: {answer}', { answer: card.answerText.replace(/[.\s]*$/, '.') }),
  },
  gap: {
    Card: GapCard,
    ready: picked,
    check: (card, value) => value === card.gap.answer,
    correction: (card) => say('Not quite. The missing word is {answer}.', { answer: card.answerText }),
  },
}

export const kindOf = (card) => KINDS[card.kind]
