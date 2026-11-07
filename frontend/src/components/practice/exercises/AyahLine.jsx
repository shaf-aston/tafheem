/**
 * The ayah a Qur'anic word is asked from, the word marked, and a button to hear it recited. Only for a question that
 * carries its place ([surah, ayah, word]: lib/quiz/quiz.js buildQuestion); the Arabic is the reader's own, and nothing
 * is drawn until it arrives or if it fails. Arabic only: the English would give the meaning away.
 */
import { useQuery } from '@tanstack/react-query'

import { quranAyahQuery } from '../../../api'
import { ayahAudioUrl, play } from '../../../lib/quran/ayahAudio'
import { sayIn } from '../../../lib/text/say'
import MarkedAyah from '../../ui/text/MarkedAyah'
import SmallButton from '../../ui/buttons/SmallButton'

const say = sayIn('en')

export default function AyahLine({ ayah: [surah, ayah, wordNumber] }) {
  const { data } = useQuery(quranAyahQuery(surah, ayah))
  if (!data?.words?.length) return null
  return (
    <div className="grow-ayah-line">
      <MarkedAyah words={data.words} word={wordNumber} accent="var(--w)" className="grow-ayah-line-ar" />
      <SmallButton onClick={() => play(ayahAudioUrl(surah, ayah))}>
        <span aria-hidden="true">▶</span> {say('Listen')} <span className="tabular-nums">{surah}:{ayah}</span>
      </SmallButton>
    </div>
  )
}
