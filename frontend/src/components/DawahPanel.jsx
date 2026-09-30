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
 * timelines' reference row (pieces in components/dawah, wording in dawah.json): a Qur'an reference opens the ayah itself. A matching
 * IslamQA fatwa is linked at the foot as further reading.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { dawahQuery } from '../api'
import { useRemembered } from '../lib/useRemembered'
import { matches } from '../lib/dawahSearch'
import knobs from '../dawah.json'

import SectionHeader from './ui/SectionHeader'
import SearchBox from './ui/SearchBox'
import ErrorAlert from './ui/ErrorAlert'
import EmptyState from './ui/EmptyState'
import { AnalyzerSkeleton } from './ui/Skeleton'
import TopicTile from './dawah/TopicTile'
import QuestionList from './dawah/QuestionList'
import Answer from './dawah/Answer'

const { copy } = knobs

export default function DawahPanel({ accent, incoming, arrival, onGo, onVisit }) {
  const { data, isPending, isError, error, refetch } = useQuery(dawahQuery)
  const [topicId, setTopicId] = useState(null)
  const [questionId, setQuestionId] = useState(null)
  const [query, setQuery] = useState('')
  const [mode, setMode] = useRemembered('dawah-mode', knobs.modes.map((m) => m.id), knobs['reading-mode'])

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
      <ErrorAlert title={copy['load-failed']} error={error} fallback={copy.unreachable} onRetry={refetch} />
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
    <div className="panel" style={{ '--c': accent }}>
      <SectionHeader
        title={copy.title}
        arabic={copy.arabic}
        subtitle={copy.subtitle}
      />

      <SearchBox
        id="dawah-search"
        label={copy.search}
        placeholder={copy['search-hint']}
        value={query}
        onChange={setQuery}
        accent={accent}
      />

      {!searching && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {data.topics.map((topic, i) => (
            <TopicTile key={topic.id} topic={topic} index={i} selected={topic.id === topicId}
              onPick={pickTopic} />
          ))}
        </div>
      )}

      {searching && rows.length === 0 && <EmptyState>{copy['no-match']}</EmptyState>}

      {rows.length > 0 && (
        <div className="grid md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] gap-5 items-start">
          <nav aria-label={copy.questions}>
            <QuestionList rows={rows} current={open.question.id} onPick={read} />
          </nav>
          <Answer {...open} library={data} accent={accent} onGo={onGo} step={step} mode={mode} modes={knobs.modes} onMode={setMode} copy={copy} />
        </div>
      )}
    </div>
  )
}
