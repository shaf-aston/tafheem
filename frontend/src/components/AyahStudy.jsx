/**
 * One ayah, studied: what each word is, how the words join, and what the ayah
 * is about. QuranReader shows it beside the surah, or under it on a phone;
 * the ayah's own line and its English are already on the page beside it, its
 * recitation is the reader's bar and its source the reader's header, so none
 * of them is drawn again here.
 *
 * It asks for its own ayah, the word-by-word grammar the surah leaves out.
 * Key it by the ayah where it is used, so the open word starts shut each time.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getQuranTarkeeb, quranAyahQuery } from '../api'
import { posLabel } from '../lib/grammarTerms'
import { posColor } from '../lib/roleColors'

import WordCard from './WordCard'
import TarkeebFigure from './TarkeebFigure'
import SourceBadge from './ui/SourceBadge'
import AyahTafsir from './AyahTafsir'
import { isQuranic } from '../lib/arabicText'
import ArabicText from './ui/ArabicText'
import CloseButton from './ui/CloseButton'
import ErrorAlert from './ui/ErrorAlert'
import { Skeleton } from './ui/Skeleton'

/** The word a key names, or undefined. Keys are the word's own `position`. */
const wordByKey = (words, key) =>
  key == null ? undefined : words.find((w, i) => (w.position || i) === key)

export default function AyahStudy({ surah, ayah, onGo, onClose, accent }) {
  const { data, isPending, isError, error, refetch } = useQuery(quranAyahQuery(surah, ayah))
  // One word open at a time. A closed chip stays a word you can read; the full
  // grammar only appears for the word actually being asked about.
  const [openWord, setOpenWord] = useState(null)
  const opened = data && wordByKey(data.words, openWord)
  const toggle = (key) => setOpenWord(openWord === key ? null : key)

  return (
    <div className="space-y-4">
      <header className="flex items-center justify-between gap-3">
        <h3 className="font-semibold text-[var(--text)]">
          Study <span className="ml-2 font-mono type-small text-[var(--text-faint)]">{surah}:{ayah}</span>
        </h3>
        <CloseButton onClick={onClose} aria-label="Close the study" />
      </header>

      {isPending && <Skeleton className="h-32" />}
      {isError && (
        <ErrorAlert inline title="Could not load this ayah's words" error={error} onRetry={() => refetch()} />
      )}

      {data && (
        <>
          {/* Every word's English always here; a tap opens its full grammar
              under the chips, in the flow rather than floating over them. */}
          <div
            className="flex flex-wrap gap-2 peer-dim"
            dir="rtl"
            lang="ar"
            data-script={isQuranic(data.words.map((w) => w.arabic).join(' ')) ? 'quran' : undefined}
          >
            {data.words.map((w, i) => {
              const key = w.position || i
              return <WordChip key={key} word={w} index={i} open={openWord === key} onToggle={() => toggle(key)} />
            })}
          </div>
          {opened && <WordCard word={opened} onGo={onGo} onClose={() => setOpenWord(null)} exclude="quran" />}
          <div className="flex items-center gap-3 flex-wrap">
            <p className="text-xs text-[var(--text-faint)]">Tap any word for its full grammar and its root</p>
          </div>
        </>
      )}

      <AyahTarkeeb surah={surah} ayah={ayah} />

      {/* Last on purpose. The grammar above answers what the words are and
          do; this answers what the ayah is about. */}
      <AyahTafsir surah={surah} ayah={ayah} accent={accent} defaultOpen />
    </div>
  )
}

/**
 * How this ayah's words join into one another.
 *
 * Separate from the word grid above on purpose: that grid says what each word
 * IS, this says what the words DO to each other. They are different questions,
 * and the app used to answer only the first while calling it the second.
 *
 * What the rules could not join is not hidden. The count below says how much of
 * the ayah is actually accounted for, and every unmade join is drawn open.
 */
function AyahTarkeeb({ surah, ayah }) {
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['tarkeeb', surah, ayah],
    queryFn: () => getQuranTarkeeb(surah, ayah),
  })

  // A failed fetch used to return null here, the same as an ayah with no tree,
  // so a dropped connection read as "this ayah has no joins". Now it says so.
  if (!isPending && !isError && !data?.tree) return null

  // Why a join is open depends on who did the work; said in a hover, not a paragraph.
  const openWhy = data?.source?.key === 'treebank'
    ? 'Left open by the people who worked this ayah out.'
    : 'Worked out by rule from each word’s own tags, which never link one word to another. Drawn open, not hidden.'

  return (
    <section className="space-y-3 pt-2">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h3 className="text-sm text-[var(--text-dim)]">
          How the words join <ArabicText size="sm" className="text-[var(--text)]">التَّرْكِيْب</ArabicText>
        </h3>
        {data && <SourceBadge source={data.source} />}
      </div>

      {isPending && <Skeleton className="h-40" />}
      {isError && (
        <ErrorAlert inline title="Could not load the word joins" error={error} onRetry={() => refetch()} />
      )}
      {data?.tree && (
        <TarkeebFigure tarkeeb={data} openWhy={openWhy} />
      )}
    </section>
  )
}

function WordChip({ word, index, open, onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-expanded={open}
      style={{ '--i': index, '--c': posColor(word.pos) }}
      className={`word rise-in flex flex-col items-center gap-1 p-2.5
        rounded-[var(--radius-md)] bg-[var(--surface)] border transition-colors
        ${open ? 'word-open border-[var(--c)]' : 'border-[var(--border)]'}`}
    >
      <ArabicText className="text-[var(--text)] leading-tight">{word.arabic}</ArabicText>
      {word.pos && (
        <ArabicText size="tiny" style={{ color: 'var(--c)' }}>{posLabel(word.pos)}</ArabicText>
      )}
      {word.meaning && (
        <span className="type-small text-[var(--text-dim)] max-w-[7rem] text-center" lang="en" dir="ltr">
          {word.meaning}
        </span>
      )}
    </button>
  )
}
