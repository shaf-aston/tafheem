/**
 * An Arabic sentence, analysed: the bracket picture of how its words join, then
 * a card for each word. One `/api/analyze` request returns both, so they are the
 * same reading. The picture is left out when nothing could be joined.
 */
import { Fragment, useLayoutEffect, useRef, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import { analyzeIraab, generatePractice, translateSentence } from '../../api'
import { errorMessage, errorStatus } from '../../lib/api/apiError'
import { buildIraabExportText } from '../../lib/nahw/iraabExport'
import { bareForm } from '../../lib/text/arabicText'
import { UNNAMED, caseLabel, isUnnamed, reading } from '../../lib/nahw/grammarTerms'
import { arc } from '../../lib/nahw/govArc'
import { roleVar } from '../../lib/nahw/roleColors'
import { useRemembered } from '../../lib/store/useRemembered'
import { useTarkeebView } from '../../lib/nahw/useTarkeebView'
import { useArrivalEffect } from '../../lib/nav/useArrival'

import SourceBadge from '../ui/SourceBadge'
import TarkeebFigure from './tarkeeb/TarkeebFigure'
import TarkeebTools from './tarkeeb/TarkeebTools'
import PracticePanel from './PracticePanel'
import SentenceMeaning from '../dictionary/SentenceMeaning'
import WordPeek from './WordPeek'
import WordCard from './WordCard'
import ArabicText from '../ui/ArabicText'
import BookPath from './BookPath'
import CopyButton from '../ui/CopyButton'
import Disclosure from '../ui/Disclosure'
import ErrorAlert from '../ui/ErrorAlert'
import ExampleChips from '../ui/ExampleChips'
import MicButton from '../ui/MicButton'
import SearchBox from '../ui/SearchBox'
import FlagButton from '../ui/FlagButton'
import { AnalyzerSkeleton } from '../ui/Skeleton'

const EXAMPLES = [
  { arabic: 'ضَرَبَ زيدٌ عمراً', meaning: 'Zayd struck ʿAmr' },
  { arabic: 'الكِتَابُ مُفِيدٌ', meaning: 'The book is useful' },
  { arabic: 'إِنَّ اللهَ غَفُورٌ رَحِيمٌ', meaning: 'Indeed Allah is Forgiving, Merciful' },
  { arabic: 'ذَهَبَ الطَّالِبُ إِلَى الْمَدْرَسَةِ', meaning: 'The student went to school' },
]

// What the word row draws: each word's role, or arcs from governor to governed.
const LENSES = ['roles', 'governs']

export default function IraabAnalyzer({ accent, onGo, onVisit, analyse = null }) {
  const [sentence, setSentence] = useState(analyse ?? '')
  const [selectedWord, setSelectedWord] = useState(null)
  // A sentence analysed is a place reached; the trail shortens it to fit.
  const analyze = useMutation({
    mutationFn: analyzeIraab,
    onSuccess: (_, asked) => onVisit?.(asked),
  })
  const practice = useMutation({ mutationFn: generatePractice })

  const submit = () => {
    const trimmed = sentence.trim()
    if (trimmed) analyze.mutate(trimmed)
  }

  const runExample = (text) => {
    setSentence(text)
    analyze.mutate(text)
  }

  // A sentence handed over from the wide view is analysed on arrival; the box
  // is already filled from the same prop. Once per sentence, not per return to the tab.
  useArrivalEffect(analyse, () => {
    if (analyse) analyze.mutate(analyse)
  })

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        {/* The same field as Dictionary and Daleel, grown to a textarea: see
            ui/SearchBox's multiline mode. */}
        <SearchBox
          id="iraab-input"
          label="Arabic sentence"
          verb="analyse"
          placeholder="اكتب جملة عربية هنا..."
          value={sentence}
          onChange={setSentence}
          onSubmit={submit}
          onClear={() => { setSentence(''); analyze.reset(); practice.reset() }}
          busy={analyze.isPending}
          accent={accent}
          arabic
          multiline
        >
          <MicButton
            onHeard={({ text }) => setSentence(text)}
            accent={accent}
            title="Say the sentence"
          />
        </SearchBox>

        <ExampleChips examples={EXAMPLES} onPick={runExample} accent={accent} />
      </div>

      {analyze.isError && <AnalyzeError error={analyze.error} onRetry={submit} />}
      {analyze.isPending && <AnalyzerSkeleton />}

      <div aria-live="polite">
        {analyze.data && !analyze.isPending && (
          <AnalysisResults
            data={analyze.data}
            accent={accent}
            onGo={onGo}
            onWordClick={setSelectedWord}
            picked={analyze.data.words.indexOf(selectedWord)}
            practice={practice}
            detail={selectedWord && (
              <WordCard word={selectedWord} onClose={() => setSelectedWord(null)} onGo={onGo} exclude="nahw" />
            )}
          />
        )}
      </div>
    </div>
  )
}

function AnalyzeError({ error, onRetry }) {
  const status = errorStatus(error)
  return (
    <ErrorAlert title={status === 504 ? 'Timed out' : 'Analysis failed'} onRetry={onRetry}>
      <div>{errorMessage(error)}</div>
    </ErrorAlert>
  )
}

// `detail` is the opened word's card, drawn right under the grid it was
// tapped in rather than after the practice block, where a tap looked ignored.
function AnalysisResults({ data, accent, onGo, onWordClick, picked, practice, detail }) {
  const [lens, setLens] = useRemembered('nahw.analyse-lens', LENSES)
  const linked = data.words.some((w) => source(w) !== undefined)
  const governs = linked && lens === 'governs'
  const view = useTarkeebView(data.tree)
  const meaning = useSentenceMeaning(data.sentence)
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        {data.summary && (
          <div
            className="rise-in flex items-center gap-2 text-sm px-3 py-2 rounded-[var(--radius-md)]
              bg-[var(--surface)] border border-[var(--border)]"
          >
            <span className="text-[var(--text-faint)] text-xs uppercase tracking-wide">Sentence</span>
            <span className="text-[var(--text)]">{data.summary}</span>
            <SourceBadge source={data.source} />
          </div>
        )}
        <div className="flex items-center gap-2">
          {data.tree && <TarkeebTools view={view} />}
          <CopyButton text={buildIraabExportText(data)} />
        </div>
      </div>

      {data.tree && (
        // An ayah drawn from its record carries the words the book supplies,
        // (هُوَ) or an elided khabar, and the mark it writes them with.
        <ChartWithPeek data={data} view={view} glosses={meaning.data?.words}
          onMore={onWordClick} onLookup={onGo && ((w) => onGo('dict', w))} />
      )}
      <EnglishMeaning meaning={meaning} accent={accent} onGo={onGo} />
      <WordGrid words={data.words} onClick={onWordClick} governs={governs} picked={picked}
        corner={linked && (
          <FlagButton value={governs} onChange={(on) => setLens(on ? 'governs' : 'roles')} accent={accent}
            title="Draw arrows from each governor to the word it governs">
            see governance
          </FlagButton>
        )} />
      <p className="text-center type-small text-[var(--text-faint)]">
        {governs && picked >= 0 && source(data.words[picked]) !== undefined
          ? <GovernsWhy words={data.words} i={picked} />
          : 'Tap a word for breakdown'}
      </p>
      {detail}

      <FullIraabTable words={data.words} onRowClick={onWordClick} />
      <PracticePanel practice={practice} sentence={data.sentence} accent={accent} />
    </div>
  )
}

// The sentence in English, asked of the dictionary as soon as it is analysed:
// the same answer the Dictionary tab gives a sentence. Its word-by-word list is
// also what the chart shows on hover, so the one request serves both.
function useSentenceMeaning(sentence) {
  return useQuery({
    queryKey: ['dictionary-sentence', sentence],
    queryFn: () => translateSentence(sentence),
    enabled: Boolean(sentence),
    staleTime: Infinity,
  })
}

// The English straight under the analysis: the sentence card already says what it
// is, so no heading names it again.
function EnglishMeaning({ meaning, accent, onGo }) {
  if (!meaning.data?.words) return null
  return (
    <section aria-label="English meaning" className="rise-in">
      <SentenceMeaning data={meaning.data} accent={accent} onGo={onGo} bare
        onLookup={(w) => onGo?.('dict', w)} />
    </section>
  )
}

// The written word a chart word is: the analysis lists the words on the page in
// order, so the nth is the one, unless the two spellings disagree (a word the
// parser split differently), when the first with the same letters is.
function nthWord(list, nth, text, key) {
  const same = (item) => item && bareForm(item[key]) === bareForm(text)
  return same(list?.[nth]) ? list[nth] : list?.find(same)
}

// The chart, with a tapped word answered in a small panel under it, in place.
function ChartWithPeek({ data, view, glosses, onMore, onLookup }) {
  const [peek, setPeek] = useState(null)
  const frame = useRef(null)
  const glossOf = (nth, text) => nthWord(glosses, nth, text, 'arabic')?.english
  const open = (text, nth, el) => {
    const word = nthWord(data.words, nth, text, 'word')
    if (!word) return onLookup?.(text)
    const box = frame.current.getBoundingClientRect()
    const at = el.getBoundingClientRect()
    // kept inside the frame, so the panel never hangs off a phone's edge
    const half = Math.min(144, box.width / 2)
    const x = Math.min(Math.max(at.left + at.width / 2 - box.left, half), box.width - half)
    setPeek({ word, english: glossOf(nth, text), text, at: { x, y: at.bottom - box.top + 6 } })
  }
  return (
    <div ref={frame} className="relative">
      <TarkeebFigure tarkeeb={data.tree} view={view} onWord={open} glossOf={glosses && glossOf} />
      {peek && (
        <WordPeek {...peek} onClose={() => setPeek(null)}
          onMore={() => { onMore(peek.word); setPeek(null) }}
          onLookup={() => onLookup?.(peek.text)} />
      )}
    </div>
  )
}

// The word a word takes its case from: its عامل, or the word a تابع follows.
const source = (w) => w.governor ?? w.follows ?? undefined

// "X governs Y" or "Y follows X", the typed words themselves.
function GovernsWhy({ words, i }) {
  const w = words[i]
  const from = <ArabicText size="sm" className="text-[var(--text)]">{words[source(w)].word}</ArabicText>
  const to = <ArabicText size="sm" className="text-[var(--text)]">{w.word}</ArabicText>
  return w.governor != null
    ?<>{from} governs {to}: it gives it its case.</>
    : <>{to} follows {from} and copies its case.</>
}

// Governs view: one unbroken line (arcs cannot cross a wrap) with an arc above it
// from each governor down into the word it governs; a follower's arc is dashed.
const ARC_CAP = 56 // px the tallest arc climbs above the words
function WordGrid({ words, onClick, governs, picked, corner }) {
  const lineRef = useRef(null)
  const [arcs, setArcs] = useState([])
  useLayoutEffect(() => {
    if (!governs) return undefined
    const line = lineRef.current
    function measure() {
      // Measured against the svg the arcs are drawn in, so no offsetParent can skew them.
      const box = line.querySelector('svg').getBoundingClientRect()
      const cards = [...line.querySelectorAll('.word')].map((c) => c.getBoundingClientRect())
      const at = (i) => [cards[i].left - box.left + cards[i].width / 2, cards[i].top - box.top]
      setArcs(words.flatMap((w, i) => (source(w) === undefined ? [] : [{
        i, dashed: w.governor == null, ...arc(at(source(w)), at(i), ARC_CAP),
      }])))
    }
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(line)
    // The cards rise in; measure again once they have landed.
    line.addEventListener('animationend', measure)
    document.fonts?.ready.then(measure)
    return () => { ro.disconnect(); line.removeEventListener('animationend', measure) }
  }, [governs, words])

  // `corner` sits in the card's top-right, outside the scroller so it stays put.
  return (
    <div className="relative">
    {corner && <div className="absolute top-2 right-2 z-[var(--layer-raised)] opacity-70 hover:opacity-100">{corner}</div>}
    <div
      dir="rtl"
      className={`peer-dim p-5 rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)]
        ${corner ? 'pt-12' : ''} ${governs ? 'overflow-x-auto' : ''}`}
    >
      <div
        ref={lineRef}
        style={governs ? { paddingTop: ARC_CAP + 8 } : undefined}
        className={`relative flex justify-center gap-3 ${governs ? 'flex-nowrap w-max min-w-full' : 'flex-wrap'}`}
      >
      {governs && (
        <svg className="absolute inset-0 w-full h-full overflow-visible pointer-events-none" aria-hidden="true">
          {arcs.map((a) => (
            <g key={a.i} stroke={roleVar(words[a.i].role_key)} fill="none" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round"
              className="transition-opacity" style={{ opacity: picked < 0 || picked === a.i ? 1 : 0.25 }}>
              <path d={a.d} strokeDasharray={a.dashed ? '4 5' : undefined} />
              <path d={a.head} />
            </g>
          ))}
        </svg>
      )}
      {words.map((word, i) => {
        const key = word.role_key
        return (
          <button
            key={`${word.word}-${i}`}
            type="button"
            onClick={() => onClick(word)}
            aria-label={`${word.word}, ${isUnnamed(word) ? 'not named, see why' : (word.name ?? word.role) || 'details'}`}
            style={{ '--i': i, '--c': roleVar(key) }}
            className="word rise-in role glow
              flex flex-col items-center gap-1.5 px-4 py-3 rounded-[var(--radius-md)]
              bg-[var(--surface-hi)] border"
          >
            <ArabicText className="text-glow leading-tight">{word.word}</ArabicText>
            {/* The term alone. What it means is in the glossary at the foot
                of the page, once, not under every tag. */}
            {word.role && (
              <span className="type-tiny px-2 py-0.5 rounded-full role-tag">
                {word.name ?? word.role}
              </span>
            )}
            {word.case && (
              <ArabicText size="tiny" className="text-[var(--text-faint)]">{caseLabel(word.case)}</ArabicText>
            )}
          </button>
        )
      })}
      </div>
    </div>
    </div>
  )
}

/**
 * The click lives on the row, one handler on the table body; the keyboard lives
 * on each word, a real button, so Tab reaches it and Enter opens it.
 */
const NONE = UNNAMED

// The full table's columns: the ones every screen shows side by side, then the proof,
// which a phone moves under its row.
const BESIDE = [['الكلمة', 'Word'], ['الإعراب', 'Role · case · sign'], ['الجذر', 'Root'], ['العامل', 'Governed by']]
const PROOF = ['الدليل', 'Proof']

function FullIraabTable({ words, onRowClick }) {
  const pick = (e) => {
    const row = e.target.closest('tr[data-i]')
    if (row) onRowClick(words[Number(row.dataset.i)])
  }
  return (
    <Disclosure framed label="Full table: every word, side by side" bodyClassName="overflow-x-auto [direction:rtl]">
        {/* Right to left like the books: the word first, its proof last, and the scroll
            opens on the word. Case and sign sit under the role (one reading, one cell);
            a sign that only repeats مبني is dropped. A phone has no room for the proof
            beside the rest, so it takes its own line under the word's row. */}
        <table dir="rtl" className="w-full type-small border-collapse">
          <thead>
            <tr className="type-micro text-[var(--text-faint)] border-b border-[var(--border)] align-bottom">
              {[...BESIDE, PROOF].map(([ar, en]) => (
                <th key={en} className={`text-right font-normal py-2 px-3 ${en === PROOF[1] ? 'hidden md:table-cell' : ''}`}>
                  <ArabicText size="sm" className="block text-[var(--text-dim)]">{ar}</ArabicText>
                  <span dir="ltr" className="block">{en}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody onClick={pick}>
            {words.map((w, i) => {
              const said = reading(w)  // one reading of case and sign, the same the copied text prints
              const proof = (
                <>
                  <ArabicText size="sm" className="block leading-relaxed">{w.reason || NONE}</ArabicText>
                  {w.reason && <BookPath path={w.book} />}
                </>
              )
              return (
                <Fragment key={`${w.word}-${i}`}>
                <tr
                  data-i={i}
                  style={{ '--c': roleVar(w.role_key) }}
                  className="md:border-b border-[var(--border)] cursor-pointer align-top transition-colors
                    hover:bg-[var(--surface-hi)] role"
                >
                  <td className="py-3 px-3 whitespace-nowrap">
                    <ArabicText as="button" type="button" className="rounded-[var(--radius-sm)] px-1">{w.word}</ArabicText>
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    <ArabicText size="sm" className="block" style={{ color: 'var(--c)' }}>{w.name ?? (w.role || '–')}</ArabicText>
                    {said.length > 0 && (
                      <ArabicText size="tiny" className="block mt-1 text-[var(--text-dim)]">{said.join(' · ')}</ArabicText>
                    )}
                  </td>
                  <ArabicText as="td" size="sm" className="py-3 px-3 text-[var(--text-dim)] whitespace-nowrap">{w.root || NONE}</ArabicText>
                  <ArabicText as="td" size="sm" className="py-3 px-3 text-[var(--text-dim)] whitespace-nowrap">
                    {source(w) === undefined ? NONE : <>{w.governor == null && 'تابع لـ '}{words[source(w)].word}</>}
                  </ArabicText>
                  <td className="hidden md:table-cell py-3 px-3 text-[var(--text-dim)] min-w-[var(--layout-proof)]">{proof}</td>
                </tr>
                <tr data-i={i} className="md:hidden border-b border-[var(--border)] cursor-pointer">
                  <td colSpan={BESIDE.length} className="pb-3 px-3 text-[var(--text-dim)]">{proof}</td>
                </tr>
                </Fragment>
              )
            })}
          </tbody>
        </table>
    </Disclosure>
  )
}
