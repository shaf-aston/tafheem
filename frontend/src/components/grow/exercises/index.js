/**
 * Grow's exercise kinds: a registry, so a new kind is one entry here and the
 * lesson runner learns nothing about it.
 *
 * Each kind has:
 *   Card    what is shown: ({ card, value, setValue, result }) => JSX
 *   ready   whether Check can be pressed yet, from the value picked
 *   check   whether the value is right; absent for a kind that asks nothing
 *   record  what the progress store files a checked answer under, so a word
 *           asked in Grow counts in the Quiz tab too (and the other way round)
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
