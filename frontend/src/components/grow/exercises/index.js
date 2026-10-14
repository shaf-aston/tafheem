/**
 * Exercise kinds: one entry per kind; the lesson runner knows none by name.
 *   Card    ({ card, value, setValue, result }) => JSX
 *   ready   can Check be pressed yet
 *   check   is the value right (absent: nothing asked)
 *   record  what the progress store files it under
 */
import MeaningCard from './MeaningCard'
import TeachCard from './TeachCard'

export const KINDS = {
  teach: { Card: TeachCard, ready: () => true },
  meaning: {
    Card: MeaningCard,
    ready: (value) => value != null,
    check: (card, value) => value === card.question.answerId,
    record: (card, module) => ({
      module,
      item: card.question.answerId,
      context: { bank: 'grow', world: 'words', word: card.question.answerWord },
    }),
  },
}

export const kindOf = (card) => KINDS[card.kind]
