/**
 * One ayah, studied: its text word by word, what each word is, how the words
 * join, and what the ayah is about.
 *
 * Split out of QuranLookup, which owns the other half of the tab: finding an
 * ayah (the two forms, the results, the root view). Finding and studying are
 * different jobs on different data, and holding both in one file meant every
 * change to a search box was made in the same place as the grammar of a word.
 *
 * The reader is shown one word at a time. Which word that is lives here, in
 * `openWord`, because three things read it: the ayah's own line, the grid of
 * word cards, and the one detail panel they both open. Tapping a word in either
 * place opens it in both, so the two views can never disagree about what is
 * being looked at.
 */
import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getQuranTarkeeb } from '../api'
import { useTranslation } from '../lib/useTranslation'
import { useRecitation } from '../lib/useRecitation'
import { useRecitedWord } from '../lib/useRecitedWord'
import { CORPUS_POS, posLabel } from '../lib/grammarTerms'
import { posColor } from '../lib/roleColors'
import { RECITERS, stop as stopAudio } from '../lib/ayahAudio'
import { useRemembered } from '../lib/useRemembered'
import { smartError } from '../lib/apiError'
import { scrollToEl } from '../lib/scrollToEl'

import WordCard from './WordCard'
import TarkeebDiagram from './TarkeebDiagram'
import PlayAyah from './ui/PlayAyah'
import Segmented from './ui/Segmented'
import SourceBadge from './ui/SourceBadge'
import TranslationStrip from './ui/TranslationStrip'
import { GoButton } from './ui/RootActions'
import Tooltip from './ui/Tooltip'
import AyahTafsir from './AyahTafsir'
import ArabicText from './ui/ArabicText'
import ErrorAlert from './ui/ErrorAlert'
import RetryButton from './ui/RetryButton'
import { Skeleton } from './ui/Skeleton'

/** The word a key names, or undefined. Keys are the word's own `position`. */
const wordByKey = (words, key) =>
  key == null ? undefined : words.find((w, i) => (w.position || i) === key)

export default function AyahStudy({ data, onGo, onReadSurah, accent }) {
  // One word open at a time. A closed card stays a word you can read; the full
  // grammar only appears for the word actually being asked about.
  const [openWord, setOpenWord] = useState(null)
  const opened = wordByKey(data.words, openWord)
  const toggle = (key) => setOpenWord(openWord === key ? null : key)
  // A chip far below the fold opens silently otherwise; nudge the new detail
  // into view rather than leaving the tap looking like it did nothing.
  const detailRef = useRef(null)
  useEffect(() => {
    if (opened) scrollToEl(detailRef.current, 'nearest')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [openWord])

  // The same chosen book, and the same cached surah, the reading view uses. A
  // reader who switched translation there does not have to switch it here.
  const translation = useTranslation(data.surah)
  const english = translation.textFor(data.ayah)

  // Remembered where it is chosen, like the commentary and the translation
  // are. A reader who prefers one voice prefers it on the next ayah too.
  const [reciter, chooseReciter] = useRemembered('reciter', RECITERS.map((one) => one.id))

  // When each word is recited, so the word being read aloud is lit as it is
  // read. It also settles which recording is played: word times belong to one
  // recording, not to the recitation in general.
  const recitation = useRecitation(data.surah, reciter)
  const src = recitation.urlFor(data.ayah)
  const lit = useRecitedWord(src, recitation.segmentsFor(data.ayah))

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 min-w-0">
          <PlayAyah surah={data.surah} ayah={data.ayah} reciter={reciter} accent={accent} src={src} eager />
          <span className="text-[var(--text-faint)] text-sm font-mono">{data.surah}:{data.ayah}</span>
        </div>
        <div className="flex items-center gap-3">
          {/* The way out of one ayah and into the whole surah around it. The
              same pill a root travels on, so it reads as a place to go. */}
          <GoButton onClick={() => onReadSurah(data.surah)} title="Open the whole surah, ayah by ayah">
            Read all of surah {data.surah}
          </GoButton>
        </div>
      </div>

      {/* Who is reciting. Quiet, and under the ayah's own line rather than
          beside it: the choice is made once and then never again, while the
          play button beside the number is pressed on every ayah. */}
      <Segmented
        wrap
        label="Reciter"
        options={RECITERS.map((one) => ({ id: one.id, label: one.name }))}
        value={reciter}
        // Whatever was reciting stops. Changing voice while one is talking and
        // hearing the old one carry on is the sort of thing that makes a person
        // press the button again to find out what happened.
        onChange={(id) => { stopAudio(); chooseReciter(id) }}
        accent={accent}
        className="flex-wrap"
      />

      {/* Arabic and its English are one card. The translation used to sit loose
          on the page below the card, and a reader could not tell it belonged to
          the ayah at all; inside, under a hairline, it reads as the same thing
          said twice. */}
      <div className="rise-in rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)] overflow-hidden">
        <div className="p-5">
          <AyahText
            words={data.words}
            endMark={data.end_mark}
            accent={accent}
            lit={lit}
            openWord={openWord}
            onToggle={toggle}
          />
        </div>

        {/* What it says, before what each word is doing. Full --text, not dim:
            dim over the raised strip read as washed out rather than quiet. */}
        {english && (
          <TranslationStrip source={translation.book?.source}>
            <p className="type-body text-[var(--text)] leading-relaxed">{english}</p>
          </TranslationStrip>
        )}
      </div>

      {/* The open word's grammar, in the page's own flow rather than floating
          over it. Floating put it half off the screen for a word at the line's
          right edge, and laid it across the words on the line below, so the
          next word could not be tapped. In flow it can do neither, and the
          reader's eye lands in the same place whichever word they picked. */}
      {opened && (
        <div ref={detailRef}>
          <WordCard word={opened} onGo={onGo} onClose={() => setOpenWord(null)} exclude="quran" />
        </div>
      )}

      {/* The corpus credit belongs to the word grammar, so it stands where the
          words do, not up beside the ayah number where it read as a second
          credit for the translation. */}
      <div className="flex items-center justify-center gap-3 flex-wrap">
        <p className="text-xs text-[var(--text-faint)]">
          Tap any word for its full grammar and its root
        </p>
        <SourceBadge source={data.source} />
      </div>

      <div className="flex flex-wrap justify-center gap-2 peer-dim" dir="rtl" lang="ar">
        {data.words.map((w, i) => {
          const key = w.position || i
          return (
            <WordChip
              key={key}
              word={w}
              index={i}
              open={openWord === key}
              lit={i === lit}
              onToggle={() => toggle(key)}
            />
          )
        })}
      </div>

      <div className="flex flex-wrap gap-2 justify-center text-xs">
        <span className="text-[var(--text-faint)]">Key</span>
        {CORPUS_POS.map((pos) => (
          <ArabicText key={pos} size="tiny" style={{ color: posColor(pos) }}>{posLabel(pos)}</ArabicText>
        ))}
      </div>

      <AyahTarkeeb surah={data.surah} ayah={data.ayah} />

      {/* Last on the card on purpose. The grammar above answers what the words
          are and do; this answers what the ayah is about, which is what a
          reader wants once the first two are settled rather than instead. */}
      <AyahTafsir surah={data.surah} ayah={data.ayah} accent={accent} defaultOpen />
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

  const total = data?.words.length ?? 0
  const placed = data ? Math.round(data.coverage * total) : 0
  const open = total - placed
  // Why a join is open depends on who did the work; said in a hover, not a paragraph.
  const why = data?.source?.key === 'treebank'
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
        <ErrorAlert inline title="Could not load the word joins">
          {smartError(error)}
          <RetryButton onClick={() => refetch()} />
        </ErrorAlert>
      )}
      {data?.tree && (
        <>
          <div className="p-5 rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)]">
            <TarkeebDiagram words={data.words} tree={data.tree} unwritten={data.unwritten} />
          </div>
          <p className="text-xs text-[var(--text-faint)]">
            {open === 0
              ? `All ${total} words placed.`
              : <>{placed} of {total} words placed, {open} <Tooltip text={why}><span className="underline decoration-dotted cursor-help">left open</span></Tooltip>.</>}
          </p>
        </>
      )}
    </section>
  )
}

function WordChip({ word, index, open, lit, onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-expanded={open}
      style={{ '--i': index, '--c': posColor(word.pos) }}
      className={`word rise-in flex flex-col items-center gap-1 p-2.5
        rounded-[var(--radius-md)] bg-[var(--surface)] border transition-colors
        ${open ? 'word-open border-[var(--c)]' : 'border-[var(--border)]'}
        ${lit ? 'word-lit' : ''}`}
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

/**
 * The ayah itself, word by word: hover or focus a word to see its English, tap
 * it for its full grammar, the way quran.com's reading line behaves. It reads
 * the same `data.words` the grid below does, so the two never disagree about
 * what a word is; they differ only in when they say it, a gloss on hover here,
 * every word's English always in the grid.
 */
function AyahText({ words, endMark, accent, lit, openWord, onToggle }) {
  return (
    <ArabicText as="div" size="lg" className="gloss-line text-right text-[var(--text)]">
      {words.map((word, i) => {
        const key = word.position || i
        return (
          <span key={key} style={{ '--c': posColor(word.pos) }}>
            {i > 0 && ' '}
            <button
              type="button"
              onClick={() => onToggle(key)}
              aria-expanded={openWord === key}
              className={`gloss-word${i === lit ? ' gloss-word-lit' : ''}`}
            >
              {/* The printed spelling, waqf marks included where the mushaf
                  carries one; falls back to the corpus spelling if a build
                  predates that data. */}
              {word.uthmani || word.arabic}
              {word.meaning && (
                <span className="gloss-tip" lang="en" dir="ltr">{word.meaning}</span>
              )}
            </button>
          </span>
        )
      })}
      {endMark && (
        <span style={{ color: accent }} aria-hidden="true"> {endMark}</span>
      )}
    </ArabicText>
  )
}
