/**
 * An everyday sentence for an answered word that has no ayah: the Arabic with
 * the word marked, the English under it. Laid out like QuizAyah so the two read
 * as one kind of card. Draws nothing until the file has arrived, or for a word
 * the file does not have.
 */
import { useQuery } from '@tanstack/react-query'

import { sentencesQuery } from '../lib/quizBanks'

import ArabicText from './ui/ArabicText'
import SpeakButton from './ui/SpeakButton'

export default function QuizExample({ word, accent, say }) {
  const { data } = useQuery(sentencesQuery)
  const found = data?.[word]
  if (!found) return null
  const [arabic, english] = found
  // "before {word} after" splits into three parts; the middle one is the word.
  const [before, marked, after] = arabic.split(/[{}]/)
  // The braces only mark the word; the server takes care of quotes and colons.
  const spoken = arabic.replace(/[{}]/g, '')

  return (
    <div className="border-t border-[var(--border)] pt-3 space-y-2">
      <div className="flex items-center justify-center gap-2">
        <ArabicText as="p" size="lg" className="text-[var(--text)] text-center">
          {before}
          {/* Colour and an underline, so the word is found without seeing colour. */}
          <mark className="bg-transparent underline underline-offset-8 decoration-2" style={{ color: accent }}>
            {marked}
          </mark>
          {after}
        </ArabicText>
        <SpeakButton key={spoken} early text={spoken} />
      </div>
      <p className="type-body text-[var(--text-dim)] text-center">{english}</p>
      <p className="type-small text-[var(--text-faint)] text-center">{say('Example sentence')}</p>
    </div>
  )
}
