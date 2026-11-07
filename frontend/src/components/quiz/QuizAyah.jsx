/**
 * The ayah an answered word comes from: its Arabic with the asked word marked,
 * the Saheeh English under it, and the reference. Draws nothing until the Arabic
 * has arrived, and nothing if it fails, so there is never a placeholder or a
 * jump; the English joins when it lands.
 */
import { useQuery } from '@tanstack/react-query'

import { ayahQueries } from '../../lib/quiz/quizAyah'

import MarkedAyah from '../ui/text/MarkedAyah'
import ShowRest from '../ui/buttons/ShowRest'

export default function QuizAyah({ ayah: [surah, ayah, wordNumber], accent }) {
  const [arabicQuery, englishQuery] = ayahQueries(surah, ayah)
  const arabic = useQuery(arabicQuery)
  const english = useQuery(englishQuery)

  // Drawn once both have settled, so the card grows once; a failed English still shows the Arabic.
  if (!arabic.data || english.isPending) return null
  const text = english.data?.passages?.[0]?.text

  return (
    <div className="border-t border-[var(--border)] pt-3 space-y-2">
      <MarkedAyah words={arabic.data.words} word={wordNumber} accent={accent} size="lg" className="text-[var(--text)] text-center" />
      {text && (
        <ShowRest lines={3} accent={accent}>
          <p className="type-body text-[var(--text-dim)] text-center">{text}</p>
        </ShowRest>
      )}
      <p className="type-small text-[var(--text-faint)] text-center tabular-nums">{surah}:{ayah}</p>
    </div>
  )
}
