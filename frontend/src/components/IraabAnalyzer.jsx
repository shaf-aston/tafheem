/**
 * An Arabic sentence, analysed: the bracket picture of how its words join, then
 * a card for each word. One `/api/analyze` request returns both, so they are the
 * same reading. The picture is left out when nothing could be joined.
 */
import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { analyzeIraab, generatePractice } from '../api'
import { errorMessage, errorStatus } from '../lib/apiError'
import { buildIraabExportText } from '../lib/iraabExport'
import { caseLabel, isUnnamed } from '../lib/grammarTerms'
import { arc } from '../lib/govArc'
import { roleVar } from '../lib/roleColors'
import { useRemembered } from '../lib/useRemembered'

import SourceBadge from './ui/SourceBadge'
import TarkeebFigure from './TarkeebFigure'
import PracticePanel from './PracticePanel'
import WordCard from './WordCard'
import ArabicText from './ui/ArabicText'
import BookPath from './ui/BookPath'
import CopyButton from './ui/CopyButton'
import Disclosure from './ui/Disclosure'
import ErrorAlert from './ui/ErrorAlert'
import ExampleChips from './ui/ExampleChips'
import MicButton from './ui/MicButton'
import SearchBox from './ui/SearchBox'
import FlagButton from './ui/FlagButton'
import { AnalyzerSkeleton } from './ui/Skeleton'

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
  // is already filled from the same prop.
  useEffect(() => {
    if (analyse) analyze.mutate(analyse)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [analyse])

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        {/* The same field as Dictionary and Daleel, grown to a textarea: see
            ui/SearchBox's multiline mode. */}
        <SearchBox
          id="iraab-input"
          label="Arabic sentence"
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
function AnalysisResults({ data, accent, onWordClick, picked, practice, detail }) {
  const [lens, setLens] = useRemembered('nahw.analyse-lens', LENSES)
  const linked = data.words.some((w) => source(w) !== undefined)
  const governs = linked && lens === 'governs'
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
        <CopyButton text={buildIraabExportText(data)} />
      </div>

      {data.tree && (
        // An ayah drawn from its record carries the words the book supplies,
        // (هُوَ) or an elided khabar, and the mark it writes them with.
        <TarkeebFigure
          words={data.tree.words}
          written={data.tree.written}
          tree={data.tree.tree}
          unwritten={data.tree.unwritten}
          coverage={data.tree.coverage}
        />
      )}
      <WordGrid words={data.words} onClick={onWordClick} governs={governs} picked={picked}
        corner={linked && (
          <FlagButton value={governs} onChange={(on) => setLens(on ? 'governs' : 'roles')} accent={accent}
            title="Draw arrows from each governor to the word it governs">
            who governs whom
          </FlagButton>
        )} />
      <p className="text-center type-small text-[var(--text-faint)]">
        {governs && picked >= 0 && source(data.words[picked]) !== undefined
          ? <GovernsWhy words={data.words} i={picked} />
          : 'Tap any word for its full breakdown'}
      </p>
      {detail}

      <FullIraabTable words={data.words} onRowClick={onWordClick} />
      <PracticePanel practice={practice} sentence={data.sentence} accent={accent} />
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
      const cards = [...line.querySelectorAll('.word')]
      const at = (i) => [cards[i].offsetLeft + cards[i].offsetWidth / 2, cards[i].offsetTop]
      setArcs(words.flatMap((w, i) => (source(w) === undefined ? [] : [{
        i, dashed: w.governor == null, ...arc(at(source(w)), at(i), ARC_CAP),
      }])))
    }
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(line)
    document.fonts?.ready.then(measure)
    return () => ro.disconnect()
  }, [governs, words])

  // `corner` sits in the card's top-right, outside the scroller so it stays put.
  return (
    <div className="relative">
    {corner && <div className="absolute top-2 right-2 z-[var(--layer-raised)] opacity-70 hover:opacity-100">{corner}</div>}
    <div
      dir="rtl"
      className={`peer-dim p-5 rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)]
        ${governs ? 'overflow-x-auto' : ''}`}
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
            aria-label={`${word.word}, ${isUnnamed(word) ? 'not named, see why' : word.role || 'details'}`}
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
                {word.role}
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
const NONE = '–'

function FullIraabTable({ words, onRowClick }) {
  const pick = (e) => {
    const row = e.target.closest('tr[data-i]')
    if (row) onRowClick(words[Number(row.dataset.i)])
  }
  return (
    <Disclosure framed label="Full table: every word, side by side" bodyClassName="overflow-x-auto">
        {/* Right to left like the books: the word first, its proof last. Case and
            sign sit under the role (one reading, one cell); a sign that only
            repeats مبني is dropped. */}
        <table dir="rtl" className="w-full type-small border-collapse">
          <thead>
            <tr className="type-micro text-[var(--text-faint)] border-b border-[var(--border)] align-bottom">
              {[['الكلمة', 'Word'], ['الإعراب', 'Role · case · sign'], ['الجذر', 'Root'], ['العامل', 'Governed by'],
                ['الدليل', 'Proof']].map(([ar, en]) => (
                <th key={en} className="text-right font-normal py-2 px-3">
                  <ArabicText size="sm" className="block text-[var(--text-dim)]">{ar}</ArabicText>
                  <span dir="ltr" className="block">{en}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody onClick={pick}>
            {words.map((w, i) => {
              const c = w.case ? caseLabel(w.case) : ''
              const reading = w.sign?.startsWith(c) ? [w.sign] : [c, w.sign].filter(Boolean)
              return (
                <tr
                  key={`${w.word}-${i}`}
                  data-i={i}
                  style={{ '--c': roleVar(w.role_key) }}
                  className="border-b border-[var(--border)] last:border-0 cursor-pointer align-top transition-colors
                    hover:bg-[var(--surface-hi)] role"
                >
                  <td className="py-3 px-3 whitespace-nowrap">
                    <ArabicText as="button" type="button" className="rounded-[var(--radius-sm)] px-1">{w.word}</ArabicText>
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    <ArabicText size="sm" className="block" style={{ color: 'var(--c)' }}>{w.role || '–'}</ArabicText>
                    {reading.length > 0 && (
                      <ArabicText size="tiny" className="block mt-1 text-[var(--text-dim)]">{reading.join(' · ')}</ArabicText>
                    )}
                  </td>
                  <ArabicText as="td" size="sm" className="py-3 px-3 text-[var(--text-dim)] whitespace-nowrap">{w.root || NONE}</ArabicText>
                  <ArabicText as="td" size="sm" className="py-3 px-3 text-[var(--text-dim)] whitespace-nowrap">
                    {source(w) === undefined ? NONE : <>{w.governor == null && 'تابع لـ '}{words[source(w)].word}</>}
                  </ArabicText>
                  <td className="py-3 px-3 text-[var(--text-dim)] min-w-[18rem]">
                    <ArabicText size="sm" className="block leading-relaxed">{w.reason || NONE}</ArabicText>
                    {w.reason && <BookPath path={w.book} />}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
    </Disclosure>
  )
}
