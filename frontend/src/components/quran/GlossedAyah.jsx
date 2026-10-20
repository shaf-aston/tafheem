import ArabicText from '../ui/ArabicText'
import GlossWord from './GlossWord'

/**
 * One ayah, with each word's English shown while the pointer rests on it.
 *
 * Arabic joins its letters inside a word and never across a space, so drawing
 * every word in its own box changes nothing about the writing. `english`
 * missing means the two sources disagreed about how many words this ayah has;
 * the ayah is then drawn plain, and a gloss is never guessed onto a word.
 */
export default function GlossedAyah({ arabic, english, learnt, allMeanings, lit = -1, peek = -1, end }) {
  const line = 'block text-right leading-loose text-[var(--text)]'
  const mark = <span className="text-[var(--c)]" aria-hidden="true"> {end}</span>
  if (!english && !learnt && lit < 0) {
    return <ArabicText size="lg" className={line}>{arabic}{mark}</ArabicText>
  }
  return (
    <ArabicText size="lg" className={`${line} gloss-line${allMeanings ? ' gloss-all' : ''}`}>
      {arabic.split(' ').map((word, i) => (
        <span key={i}>
          {i > 0 && ' '}
          <GlossWord gloss={english?.[i]} lit={i === lit} learnt={learnt?.[i]} peek={i === peek} data-i={i}>{word}</GlossWord>
        </span>
      ))}
      {mark}
    </ArabicText>
  )
}
