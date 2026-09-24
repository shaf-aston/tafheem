/**
 * An Arabic sentence, analysed: the bracket picture of how its words join, then
 * a card for each word with its role, case and the reason.
 *
 * One request brings both (`/api/analyze` returns `tree` beside `words`), so the
 * picture and the cards are the same reading and cannot contradict each other.
 * The picture is left out when the parser could join nothing.
 */
import { useCallback, useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { analyzeIraab, generatePractice } from '../api'
import { errorMessage, errorStatus } from '../lib/apiError'
import { buildIraabExportText } from '../lib/iraabExport'
import { caseLabel, ROLE_LEGEND, signLabel } from '../lib/grammarTerms'
import { roleVar } from '../lib/roleColors'

import SourceBadge from './ui/SourceBadge'
import TarkeebDiagram from './TarkeebDiagram'
import WordCard from './WordCard'
import ArabicText from './ui/ArabicText'
import CopyButton from './ui/CopyButton'
import Disclosure from './ui/Disclosure'
import ErrorAlert from './ui/ErrorAlert'
import ExampleChips from './ui/ExampleChips'
import MicButton from './ui/MicButton'
import RetryButton from './ui/RetryButton'
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

  const submit = useCallback(() => {
    const trimmed = sentence.trim()
    if (trimmed) analyze.mutate(trimmed)
  }, [sentence, analyze])

  const runExample = (text) => {
    setSentence(text)
    analyze.mutate(text)
  }

  // A sentence arriving from the wide view is analysed on sight, so the reader
  // does not have to press anything to see the close-up of what they clicked.
  // Analysing it is the whole point of having been handed it, so it happens on
  // arrival. The box is already filled from the same prop, so nothing is set here.
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
            onHeard={({ text }) => setSentence(text || '')}
            accent={accent}
            title="Say the sentence"
          />
        </SearchBox>

        <ExampleChips examples={EXAMPLES} onPick={runExample} accent={accent} />
      </div>

      {!sentence && !analyze.data && <RoleLegend accent={accent} intro />}

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
    <ErrorAlert title={status === 504 ? 'Timed out' : 'Analysis failed'}>
      <div>{errorMessage(error)}</div>
      {status === 500 && (
        <div className="text-xs mt-2">
          The richer explanation could not be produced right now. The offline analysis above still stands.
        </div>
      )}
      <RetryButton onClick={onRetry} />
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

      <RoleLegend accent={accent} />
      {data.tree && <SentencePicture tree={data.tree} />}
      <WordGrid words={data.words} onClick={onWordClick} />
      <p className="text-center type-small text-[var(--text-faint)]">
        Tap any word for its full breakdown
      </p>
      {detail}

      <FullIraabTable words={data.words} onRowClick={onWordClick} />
      <PracticeSection practice={practice} sentence={data.sentence} accent={accent} />
    </div>
  )
}

/**
 * The same reading, drawn: which words join into a unit and what that unit does.
 *
 * It sits above the cards because it is the wider view of the one sentence, and
 * it comes back with them from the same request, so the two can never disagree.
 * A word no rule could name is drawn as a gap by the diagram itself, and the
 * line underneath says how much was placed rather than letting a tidy picture
 * imply everything was.
 */
function SentencePicture({ tree }) {
  const placed = Math.round((tree.coverage ?? 0) * 100)
  return (
    <div className="space-y-2">
      <div
        className="rise-in p-5 rounded-[var(--radius-lg)] bg-[var(--surface)]
          border border-[var(--border)]"
      >
        <TarkeebDiagram words={tree.words} tree={tree.tree} />
      </div>
      <p className="text-center type-small text-[var(--text-faint)]">
        {placed === 100 ? 'Every word placed' : `${placed}% of the words placed, the rest left open`}
      </p>
    </div>
  )
}

function RoleLegend({ accent, intro = false }) {
  return (
    <div className="flex flex-wrap gap-1.5 items-center" style={{ '--c': accent }}>
      <span className="text-[var(--text-faint)] text-xs shrink-0">
        {intro ? 'Colours you will see:' : 'Key'}
      </span>
      {ROLE_LEGEND.map(({ arabic, key }, i) => (
        <ArabicText
          key={key}
          size="tiny"
          style={{ '--i': i, '--c': roleVar(key) }}
          className="rise-in px-2 py-0.5 rounded-full role-tag"
        >
          {arabic}
        </ArabicText>
      ))}
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
            aria-label={`${word.word}, ${word.role || 'details'}`}
            style={{ '--i': i, '--c': roleVar(key) }}
            className="word rise-in role glow
              flex flex-col items-center gap-1.5 px-4 py-3 rounded-[var(--radius-md)]
              bg-[var(--surface-hi)] border"
          >
            <ArabicText className="text-glow leading-tight">{word.word}</ArabicText>
            {/* The term alone. What it means is in the glossary at the foot
                of the page, once, not under every tag. */}
            {word.role && (
              <span className="text-xs px-2 py-0.5 rounded-full role-tag">
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
 * A row opens its word. The click lives on the row and the keyboard on the
 * word: one handler on the table body reads which row was hit, and each word
 * is a real button, so Tab reaches it and Enter opens it. The ring is the
 * browser's own :focus-visible, drawn for a key and never for a click.
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
                <ArabicText as="td" size="sm" className="py-2 px-3 text-[var(--text-dim)]">{w.sign ? signLabel(w.sign) : '–'}</ArabicText>
                <ArabicText as="td" className="py-2 px-3 text-[var(--text-dim)]">{w.root || '–'}</ArabicText>
                <td className="py-2 px-3 text-[var(--text-faint)] max-w-xs">{w.reason || '–'}</td>
              </tr>
            ))}
          </tbody>
        </table>
    </Disclosure>
  )
}

function PracticeSection({ practice, sentence, accent }) {
  return (
    <div className="border-t border-[var(--border)] pt-4">
      <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
        <div>
          <div className="text-sm font-medium text-[var(--text)]">Practice questions</div>
          <div className="text-xs text-[var(--text-faint)]">Check you followed this sentence</div>
        </div>
        <button
          type="button"
          onClick={() => practice.mutate(sentence)}
          disabled={practice.isPending}
          style={{ '--c': accent, color: accent }}
          className="px-4 py-1.5 text-sm rounded-[var(--radius-md)] border border-[var(--border)]
            hover:border-[var(--c)] disabled:opacity-50 transition-colors"
        >
          {practice.isPending ? 'Generating…' : 'Generate'}
        </button>
      </div>

      {practice.isError && (
        <p className="text-sm" style={{ color: 'var(--danger)' }}>
          {errorMessage(practice.error, 'Could not generate questions.')}
        </p>
      )}
      {practice.data && !practice.isPending && (
        <PracticeQuestions data={practice.data} accent={accent} />
      )}
    </div>
  )
}

function PracticeQuestions({ data, accent }) {
  const [revealed, setRevealed] = useState({})

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <SourceBadge source={data.source} />
      </div>
      {data.questions.map((q, i) => (
        <div
          key={i}
          style={{ '--i': i }}
          className="rise-in p-4 rounded-[var(--radius-md)] bg-[var(--surface)] border border-[var(--border)] space-y-2"
        >
          <p className="text-sm font-medium text-[var(--text)]">{i + 1}. {q.question}</p>
          {q.hint && !revealed[i] && (
            <p className="text-xs text-[var(--text-faint)] italic">Hint: {q.hint}</p>
          )}
          {revealed[i] ? (
            <div
              className="fade-in p-3 rounded-[var(--radius-sm)] text-sm"
              style={{
                color: 'var(--success)',
                background: 'color-mix(in srgb, var(--success) 10%, transparent)',
              }}
            >
              {q.answer}
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setRevealed((r) => ({ ...r, [i]: true }))}
              style={{ '--c': accent, color: accent }}
              className="text-xs underline underline-offset-2 hover:opacity-80 transition-opacity"
            >
              Show answer
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
