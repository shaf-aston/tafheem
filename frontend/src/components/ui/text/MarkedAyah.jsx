/**
 * An ayah's words with one of them marked: the word a quiz or a lesson asked
 * about, shown where it stands. `words` are the reader's own (each has a
 * "surah:ayah:word" position), drawn as they came; only the mark is added.
 */
import ArabicText from './ArabicText'
import Mark from '../display/Mark'

const numberOf = (word) => Number(String(word.position).split(':').pop())

export default function MarkedAyah({ words, word: asked, accent, ...rest }) {
  return (
    <ArabicText as="p" {...rest}>
      {words.map((word, i) => {
        const text = word.uthmani || word.arabic
        return <span key={i}>{i > 0 && ' '}{numberOf(word) === asked ? <Mark accent={accent}>{text}</Mark> : text}</span>
      })}
    </ArabicText>
  )
}
