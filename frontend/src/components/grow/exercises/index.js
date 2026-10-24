/**
 * Exercise kinds: one entry per kind; the lesson runner knows none by name.
 *   Card        ({ card, value, setValue, result }) => JSX
 *   ready       can Check be pressed yet ((value, card))
 *   check       is the value right (absent: a teach card, nothing asked)
 *   correction  what to say when wrong
 *   because     why, said after a right answer too (optional)
 * A checked card carries `record` ({ module, item, context }), what the progress store files it under.
 */
import { sayIn } from '../../../lib/text/say'
import AyahCard from './AyahCard'
import ChooseCard from './ChooseCard'
import GapCard from './GapCard'
import HadithCard from './HadithCard'
import MeaningCard from './MeaningCard'
import OrderCard from './OrderCard'
import PickCard from './PickCard'
import RuleCard from './RuleCard'
import SortCard from './SortCard'
import TeachCard from './TeachCard'

const say = sayIn('en')
const picked = (value) => value != null
const sameSet = (a, b) => a.length === b.length && a.every((one) => b.includes(one))
// A book world's question says why, right or wrong (lib/grow/bookLesson.js).
const why = (card) => card.why

export const KINDS = {
  teach: { Card: TeachCard },
  hadith: { Card: HadithCard },
  ayah: { Card: AyahCard },
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
  rule: { Card: RuleCard },
  choose: { Card: ChooseCard, ready: picked, check: (card, value) => value === card.answer, correction: why, because: why },
  pick: {
    Card: PickCard,
    ready: (value) => Boolean(value?.length),
    check: (card, value) => sameSet(value, card.options.filter((option) => option.right).map((option) => option.id)),
    correction: why,
    because: why,
  },
  sort: {
    Card: SortCard,
    ready: (value, card) => card.items.every((_, i) => value?.[i]),
    check: (card, value) => card.items.every((item, i) => value[i] === item.into),
    correction: why,
    because: why,
  },
  order: {
    Card: OrderCard,
    ready: (value, card) => value?.length === card.steps.length,
    check: (card, value) => card.steps.every((step, i) => value[i] === step),
    correction: (card) => `${card.why} ${card.steps.join(' → ')}.`,
    because: why,
  },
}

export const kindOf = (card) => KINDS[card.kind]
