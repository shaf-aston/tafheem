/**
 * The teacher's Nahw notes: read whole, read with pieces hidden, or drilled as
 * cards. This file fetches the notes, picks the topic and the mode, and holds
 * which pieces are hidden; NoteBlock draws a block and NoteCards runs the cards.
 *
 * The switches are the roles the backend declares (roles.json), shown only
 * where this topic marks at least one piece of that role, so no switch here
 * ever does nothing.
 */
import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getNotes } from '../api'
import { smartError } from '../lib/apiError'
import { NOTES, cardsOf, rolesUsed } from '../lib/notes'
import { scrollToEl } from '../lib/scrollToEl'
import { readViewParam, writeViewParams } from '../lib/tabUrl'
import { useRemembered, useRememberedFlag } from '../lib/useRemembered'

import NoteBlock from './NoteBlock'
import NoteCards from './NoteCards'
import ArabicText from './ui/ArabicText'
import Chip from './ui/Chip'
import EmptyState from './ui/EmptyState'
import FlagButton from './ui/FlagButton'
import ErrorAlert from './ui/ErrorAlert'
import RetryButton from './ui/RetryButton'
import Segmented from './ui/Segmented'
import { AnalyzerSkeleton } from './ui/Skeleton'
import SmallButton from './ui/SmallButton'

const MODES = [
  { id: 'read', label: 'Read' },
  { id: 'test', label: 'Hide and test' },
  { id: 'cards', label: 'Flashcards' },
]
const MODE_IDS = MODES.map((m) => m.id)
const NOTHING = new Set()

export default function NotesPanel({ accent, topic: asked, onTamreen }) {
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['notes'],
    queryFn: getNotes,
    staleTime: Infinity,
  })

  const [savedMode, rememberMode] = useRemembered('notes-mode', MODE_IDS)
  const [mode, setModeNow] = useState(() => readViewParam('notes-mode', MODE_IDS) ?? savedMode)
  const setMode = (id) => { setModeNow(id); rememberMode(id) }

  const [savedTopic, rememberTopic] = useRemembered('notes-topic')
  const [topicId, setTopicNow] = useState(() => asked ?? readViewParam('note') ?? savedTopic)
  const setTopic = (id) => { setTopicNow(id); rememberTopic(id) }

  const [hidden, setHidden] = useState(() => new Set(NOTES.hide))
  const [english, setEnglish] = useRememberedFlag('notes-english', true)

  // A topic handed over from Tamreen replaces whatever was open.
  const [lastAsked, setLastAsked] = useState(asked)
  if (asked !== lastAsked) {
    setLastAsked(asked)
    if (asked) setTopicNow(asked)
  }

  const topics = data?.topics ?? []
  const topic = topics.find((t) => t.id === topicId) ?? topics[0]

  useEffect(() => {
    writeViewParams({ note: topic?.id ?? '', 'notes-mode': mode === 'read' ? '' : mode })
  }, [topic?.id, mode])

  // What has been revealed belongs to one topic, mode and choice of what to
  // hide; change any of them and everything is hidden again.
  const scope = `${topic?.id}:${mode}:${[...hidden].sort().join()}`
  const [shownNow, setShownNow] = useState({ scope, keys: NOTHING })
  const revealed = shownNow.scope === scope ? shownNow.keys : NOTHING

  const used = useMemo(() => (topic ? rolesUsed(topic) : new Set()), [topic])
  const cards = useMemo(() => (topic ? cardsOf(topic, [...hidden]) : []), [topic, hidden])

  if (isPending) return <AnalyzerSkeleton />
  if (isError) {
    return (
      <ErrorAlert title="Could not load the notes">
        {smartError(error, 'The notes could not be reached.')}
        <RetryButton onClick={refetch} />
      </ErrorAlert>
    )
  }
  if (!topic) return <EmptyState>No notes are written up yet.</EmptyState>

  const toggle = (role) => setHidden((now) => {
    const next = new Set(now)
    if (next.has(role)) next.delete(role)
    else next.add(role)
    return next
  })
  const reveal = (key) => setShownNow({ scope, keys: new Set(NOTES.revealStays ? [...revealed, key] : [key]) })
  const goToPage = (page) => {
    setMode('read')
    requestAnimationFrame(() => scrollToEl(document.getElementById(`note-page-${page}`), 'top'))
  }

  const offered = data.roles.filter((role) => used.has(role.key))
  const firstOfPage = new Set()

  return (
    <div className="space-y-4" style={{ '--c': accent }}>
      <div className="flex flex-wrap gap-1.5" role="group" aria-label="Topic">
        {topics.map((t) => (
          <Chip key={t.id} accent={accent} arabic selected={t.id === topic.id} title={t.title} onClick={() => setTopic(t.id)}>
            {t.arabic}
          </Chip>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Segmented label="How to use the notes" options={MODES} value={mode} onChange={setMode} accent={accent} />
        {mode !== 'cards' && (
          <FlagButton value={english} onChange={setEnglish} accent={accent} title="Show the English under each line">
            English
          </FlagButton>
        )}
        {topic.tamreen.length > 0 && onTamreen && (
          <SmallButton onClick={onTamreen} className="ms-auto">Practise this in Tamreen</SmallButton>
        )}
      </div>

      {mode !== 'read' && (
        <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label={mode === 'cards' ? 'What to ask' : 'What to hide'}>
          <span className="type-small text-[var(--text-faint)] me-1">{mode === 'cards' ? 'Ask me' : 'Hide'}</span>
          {offered.map((role) => (
            <Chip key={role.key} accent={accent} selected={hidden.has(role.key)} title={`${role.en}: ${role.hint}`} onClick={() => toggle(role.key)}>
              {role.en}
            </Chip>
          ))}
          {mode === 'test' && revealed.size > 0 && (
            <SmallButton onClick={() => setShownNow({ scope, keys: NOTHING })} className="ms-auto">Hide again</SmallButton>
          )}
        </div>
      )}

      <header className="space-y-0.5">
        {/* The topic's own Arabic name sits opposite its English one: the chips
            above are Arabic only, so without it the heading is the one place
            the two names never meet. */}
        <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
          <h3 className="text-lg font-semibold">{topic.title}</h3>
          {topic.arabic && <ArabicText size="lg" className="font-semibold text-[var(--text-dim)]">{topic.arabic}</ArabicText>}
        </div>
        <p className="type-small text-[var(--text-faint)]">{topic.pages} {topic.pages === 1 ? 'page' : 'pages'} of the teacher&apos;s notes</p>
      </header>

      {mode === 'cards' ? (
        <NoteCards key={`${topic.id}:${[...hidden].sort().join()}`} cards={cards} accent={accent} onPage={goToPage} />
      ) : (
        <div className="space-y-5">
          {topic.blocks.map((block) => {
            const anchor = firstOfPage.has(block.page) ? undefined : `note-page-${block.page}`
            firstOfPage.add(block.page)
            return (
              <div key={block.id} id={anchor} className="scroll-mt-24">
                <NoteBlock
                  topicId={topic.id}
                  block={block}
                  testing={mode === 'test'}
                  hidden={hidden}
                  revealed={revealed}
                  onReveal={reveal}
                  english={english}
                />
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
