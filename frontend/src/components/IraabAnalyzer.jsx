/**
 * An Arabic sentence, analysed: the bracket picture of how its words join, then
 * a card for each word. One `/api/analyze` request returns both, so they are the
 * same reading. The picture is left out when nothing could be joined.
 */
import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { analyzeIraab, generatePractice } from '../api'
import { errorMessage, errorStatus } from '../lib/apiError'
import { buildIraabExportText } from '../lib/iraabExport'
import { caseLabel, isUnnamed } from '../lib/grammarTerms'
import { roleVar } from '../lib/roleColors'

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
import { AnalyzerSkeleton } from './ui/Skeleton'

const EXAMPLES = [
  { arabic: 'ضَرَبَ زيدٌ عمراً', meaning: 'Zayd struck ʿAmr' },
  { arabic: 'الكِتَابُ مُفِيدٌ', meaning: 'The book is useful' },
  { arabic: 'إِنَّ اللهَ غَفُورٌ رَحِيمٌ', meaning: 'Indeed Allah is Forgiving, Merciful' },
  { arabic: 'ذَهَبَ الطَّالِبُ إِلَى الْمَدْرَسَةِ', meaning: 'The student went to school' },
]

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
function AnalysisResults({ data, accent, onWordClick, practice, detail }) {
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
          tree={data.tree.tree}
          unwritten={data.tree.unwritten}
          coverage={data.tree.coverage}
        />
      )}
      <WordGrid words={data.words} onClick={onWordClick} />
      <p className="text-center type-small text-[var(--text-faint)]">
        Tap any word for its full breakdown
      </p>
      {detail}

      <FullIraabTable words={data.words} onRowClick={onWordClick} />
      <PracticePanel practice={practice} sentence={data.sentence} accent={accent} />
    </div>
  )
}

function WordGrid({ words, onClick }) {
  return (
    <div
      dir="rtl"
      className="peer-dim flex flex-wrap justify-center gap-3 p-5 rounded-[var(--radius-lg)]
        bg-[var(--surface)] border border-[var(--border)]"
    >
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
  )
}

/**
 * The click lives on the row, one handler on the table body; the keyboard lives
 * on each word, a real button, so Tab reaches it and Enter opens it.
 */
function FullIraabTable({ words, onRowClick }) {
  const pick = (e) => {
    const row = e.target.closest('tr[data-i]')
    if (row) onRowClick(words[Number(row.dataset.i)])
  }
  return (
    <Disclosure framed label="Full table: every word, side by side" bodyClassName="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="text-[var(--text-faint)] text-xs uppercase tracking-wide border-b border-[var(--border)]">
              <ArabicText as="th" className="text-right py-2 px-3">الكلمة</ArabicText>
              <th className="text-left py-2 px-3">Role</th>
              <th className="text-left py-2 px-3">Case</th>
              <th className="text-left py-2 px-3">Sign</th>
              <th className="text-left py-2 px-3">Root</th>
              <th className="text-left py-2 px-3">Proof (الدليل)</th>
            </tr>
          </thead>
          <tbody onClick={pick}>
            {words.map((w, i) => (
              <tr
                key={`${w.word}-${i}`}
                data-i={i}
                style={{ '--c': roleVar(w.role_key) }}
                className="border-b border-[var(--border)] cursor-pointer transition-colors
                  hover:bg-[var(--surface-hi)] role"
              >
                <td className="py-2 px-3 text-right">
                  <ArabicText as="button" type="button" className="rounded-[var(--radius-sm)] px-1">{w.word}</ArabicText>
                </td>
                <td className="py-2 px-3" style={{ color: 'var(--c)' }}>{w.role || '–'}</td>
                <ArabicText as="td" size="sm" className="py-2 px-3 text-[var(--text-dim)]">{w.case ? caseLabel(w.case) : '–'}</ArabicText>
                <ArabicText as="td" size="sm" className="py-2 px-3 text-[var(--text-dim)]">{w.sign || '–'}</ArabicText>
                <ArabicText as="td" className="py-2 px-3 text-[var(--text-dim)]">{w.root || '–'}</ArabicText>
                <td className="py-2 px-3 text-[var(--text-faint)] max-w-xs">
                  {w.reason || '–'}
                  {w.reason && <BookPath path={w.book} />}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
    </Disclosure>
  )
}
