/**
 * Dawah: the questions most often put to Islam, each with a reply and its evidence.
 *
 * Topic tiles first, then the topic's questions beside the answer being read.
 * Typing in the box searches every topic at once, so a question heard in a
 * conversation is found without knowing where it is filed.
 *
 * The place in the tab is the question's id (ids are unique across topics), so
 * ?tab=dawah&q=who-made-god opens that answer and the back arrow steps through
 * the answers read. Each point carries its own evidence underneath, reusing the
 * timelines' reference row: a Qur'an reference opens the ayah itself. A matching
 * IslamQA fatwa is linked at the foot as further reading.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getDawah } from '../api'
import { smartError } from '../lib/apiError'
import { useRemembered } from '../lib/useRemembered'
import knobs from '../dawah.json'

import SectionHeader from './ui/SectionHeader'
import SearchBox from './ui/SearchBox'
import Segmented from './ui/Segmented'
import CopyButton from './ui/CopyButton'
import Chip from './ui/Chip'
import ArabicText from './ui/ArabicText'
import SourceBadge from './ui/SourceBadge'
import ErrorAlert from './ui/ErrorAlert'
import RetryButton from './ui/RetryButton'
import EmptyState from './ui/EmptyState'
import { GoButton } from './ui/RootActions'
import { AnalyzerSkeleton } from './ui/Skeleton'
import TimelineRefs from './TimelineRefs'

const fold = (text) => text.toLowerCase().replace(/[^a-z0-9؀-ۿ ]/g, ' ')

// Every word typed must appear somewhere in the question, its reply or its topic.
const matches = (query, topic, question) => {
  const hay = fold(`${question.q} ${question.short} ${topic.title}`)
  return fold(query).split(/\s+/).filter(Boolean).every((word) => hay.includes(word))
}

function TopicTile({ topic, index, selected, accent, onPick }) {
  return (
    <button
      type="button"
      onClick={() => onPick(topic)}
      aria-pressed={selected}
      style={{
        '--i': index,
        borderColor: selected ? accent : undefined,
        background: selected ? `color-mix(in srgb, ${accent} 12%, var(--surface))` : undefined,
      }}
      className="rise-in lift press text-left rounded-[var(--radius-md)] border border-[var(--border)]
        bg-[var(--surface)] p-4 flex flex-col gap-2 hover:border-[var(--c)]"
    >
      <span className="flex items-baseline justify-between gap-2">
        <span className="type-figure font-semibold" style={{ color: accent }}>{topic.questions.length}</span>
        <ArabicText size="sm" className="arabic-inline text-[var(--text-faint)]">{topic.arabic}</ArabicText>
      </span>
      <span className="font-semibold text-[var(--text)]">{topic.title}</span>
      <span className="type-small text-[var(--text-dim)] leading-snug">{topic.blurb}</span>
    </button>
  )
}

function QuestionList({ rows, current, accent, onPick }) {
  return (
    <ol className="space-y-1">
      {rows.map(({ topic, question }, i) => {
        const on = question.id === current
        return (
          <li key={question.id} className="rise-in" style={{ '--i': i }}>
            <button
              type="button"
              onClick={() => onPick(question.id)}
              aria-current={on ? 'true' : undefined}
              style={on ? { borderColor: accent, color: 'var(--text)' } : undefined}
              className="press w-full text-left rounded-[var(--radius-sm)] border-s-2 border-transparent
                px-3 py-2 text-sm text-[var(--text-dim)] hover:text-[var(--text)] hover:bg-[var(--surface-hi)]
                transition-colors"
            >
              {question.q}
              {rows.some((r) => r.topic !== topic) && (
                <span className="block type-tiny text-[var(--text-faint)] mt-0.5">{topic.title}</span>
              )}
            </button>
          </li>
        )
      })}
    </ol>
  )
}

const MODES = [
  { id: 'steps', label: 'Step by step' },
  { id: 'all', label: 'All at once' },
]

// The reasoning as a numbered path. Step by step reveals one point per press,
// the way the argument would be made out loud; All at once is for reading.
function Argument({ points, library, accent, mode, onGo }) {
  const [shown, setShown] = useState(1)
  const visible = mode === 'all' ? points : points.slice(0, shown)
  return (
    <div className="space-y-3">
      <ol className="space-y-0">
        {visible.map((point, i) => (
          <li key={point.title} className="rise-in relative flex gap-3 pb-4" style={{ '--i': mode === 'all' ? i : 0 }}>
            {i < points.length - 1 && (
              <span aria-hidden="true" className="absolute start-[0.8rem] top-7 bottom-0 border-s border-[var(--border)]" />
            )}
            <span
              aria-hidden="true"
              className="relative shrink-0 w-[1.6rem] h-[1.6rem] grid place-items-center rounded-full type-tiny font-semibold text-[var(--bg)]"
              style={{ background: accent }}
            >
              {i + 1}
            </span>
            <div className="space-y-1.5 pt-0.5">
              <p className="text-[var(--text-dim)] leading-relaxed">
                <strong className="font-semibold text-[var(--text)]">{point.title}:</strong> {point.text}
              </p>
              {/* The evidence sits under the point it proves, small, so the claim reads first. */}
              <div className="flex flex-wrap items-center gap-1.5 type-small">
                <em className="text-[var(--text-faint)]">Evidence</em>
                <TimelineRefs refs={point.refs} library={library} accent={accent} onGo={onGo} className="contents" />
                {point.note && <em className="text-[var(--text-faint)]">{point.note}</em>}
              </div>
            </div>
          </li>
        ))}
      </ol>
      {mode === 'steps' && shown < points.length && (
        <div className="flex items-center gap-3 ps-10">
          <GoButton style={{ '--c': accent }} onClick={() => setShown(shown + 1)}>Next point</GoButton>
          <span className="type-small text-[var(--text-faint)]">{shown} of {points.length}</span>
        </div>
      )}
    </div>
  )
}

function Answer({ topic, question, library, accent, onGo, step, mode, onMode }) {
  const fatwa = question.islamqa
  return (
    <article key={question.id} className="fade-in rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-5 space-y-5">
      <div className="space-y-2">
        <p className="type-tiny uppercase tracking-wide" style={{ color: accent }}>{topic.title}</p>
        <h3 className="text-xl font-semibold leading-snug text-[var(--text)]">{question.q}</h3>
      </div>

      <div
        className="rounded-[var(--radius-sm)] p-4 flex gap-3 items-start justify-between"
        style={{ background: `color-mix(in srgb, ${accent} 10%, transparent)` }}
      >
        <div className="space-y-1">
          <p className="type-tiny uppercase tracking-wide text-[var(--text-faint)]">In short</p>
          <p className="text-[var(--text)] leading-relaxed">{question.short}</p>
        </div>
        <CopyButton text={question.short} label="Copy" />
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <p className="type-small font-medium text-[var(--text-dim)]">The reasoning</p>
          <Segmented label="How to read the reasoning" options={MODES} value={mode} onChange={onMode} accent={accent} />
        </div>
        <Argument key={`${question.id}-${mode}`} points={question.points} library={library} accent={accent} mode={mode} onGo={onGo} />
      </div>

      <div className="flex items-center justify-between gap-2 flex-wrap pt-3 border-t border-[var(--border)]">
        {fatwa ? (
          <Chip cite accent={accent} href={library.islamqa.cite.replace('{number}', fatwa.number)} title={fatwa.title}>
            Read more: {library.islamqa.name} {fatwa.number}
          </Chip>
        ) : <span />}
        <div className="flex gap-2">
          {step.prev && <GoButton style={{ '--c': accent }} onClick={step.prev}>Previous</GoButton>}
          {step.next && <GoButton style={{ '--c': accent }} onClick={step.next}>Next question</GoButton>}
        </div>
      </div>

      <SourceBadge source={library.source} />
    </article>
  )
}

export default function DawahPanel({ accent, incoming, arrival, onGo, onVisit }) {
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['dawah'],
    queryFn: getDawah,
    staleTime: Infinity,
  })
  const [topicId, setTopicId] = useState(null)
  const [questionId, setQuestionId] = useState(null)
  const [query, setQuery] = useState('')
  const [mode, setMode] = useRemembered('dawah-mode', MODES.map((m) => m.id), knobs['reading-mode'])

  // An arrival names a question; followed during render like the Timelines tab,
  // so a deep link paints on its answer rather than the tiles first.
  const [seenLink, setSeenLink] = useState(null)
  const link = `${arrival}:${incoming}`
  if (data && link !== seenLink) {
    setSeenLink(link)
    const home = data.topics.find((t) => t.questions.some((q) => q.id === incoming))
    if (home) {
      setTopicId(home.id)
      setQuestionId(incoming)
    }
  }

  if (isPending) return <AnalyzerSkeleton />
  if (isError) {
    return (
      <ErrorAlert title="Could not load the dawah answers">
        {smartError(error, 'The answers could not be reached.')}
        <RetryButton onClick={refetch} />
      </ErrorAlert>
    )
  }

  const all = data.topics.flatMap((topic) => topic.questions.map((question) => ({ topic, question })))
  const searching = query.trim() !== ''
  const rows = searching
    ? all.filter(({ topic, question }) => matches(query, topic, question))
    : all.filter(({ topic }) => topic.id === topicId)
  // A search whose results leave out the answer on screen opens its first match.
  const open = rows.find(({ question }) => question.id === questionId) ?? rows[0]
  const at = rows.indexOf(open)

  const read = (id) => {
    setQuestionId(id)
    onVisit?.(id)
  }
  const pickTopic = (topic) => {
    setQuery('')
    setTopicId(topic.id)
    read(topic.questions[0].id)
  }
  const step = {
    prev: at > 0 ? () => read(rows[at - 1].question.id) : null,
    next: at >= 0 && at < rows.length - 1 ? () => read(rows[at + 1].question.id) : null,
  }

  return (
    <div className="space-y-5" style={{ '--c': accent }}>
      <SectionHeader
        title="Dawah"
        arabic="دعوة"
        subtitle="Clear answers to the questions most often asked about Islam, each with its evidence."
      />

      <SearchBox
        id="dawah-search"
        label="Find a question"
        placeholder="e.g. who created God, hijab, sword"
        value={query}
        onChange={setQuery}
        accent={accent}
      />

      {!searching && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {data.topics.map((topic, i) => (
            <TopicTile key={topic.id} topic={topic} index={i} selected={topic.id === topicId}
              accent={accent} onPick={pickTopic} />
          ))}
        </div>
      )}

      {searching && rows.length === 0 && <EmptyState>No question matches that. Try fewer words.</EmptyState>}

      {rows.length > 0 && (
        <div className="grid md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] gap-5 items-start">
          <nav aria-label="Questions">
            <QuestionList rows={rows} current={open.question.id} accent={accent} onPick={read} />
          </nav>
          <Answer {...open} library={data} accent={accent} onGo={onGo} step={step} mode={mode} onMode={setMode} />
        </div>
      )}
    </div>
  )
}
