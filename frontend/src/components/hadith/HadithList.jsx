/**
 * One book's hadiths in full. The title bar stays under the app header while
 * you read: the way back, how far through you are, a jump to a number, and a
 * quiet icon that opens how the hadiths are laid out (two per row, chain hidden).
 */
import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { hadithBookQuery } from '../../api'
import { holdAtTop, scrollToEl, useOpenAtTop } from '../../lib/motion/scrollToEl'
import { topicOf } from '../../lib/hadith/hadithGrade'
import { useRememberedFlag } from '../../lib/store/useRemembered'
import { useSideBySide } from '../../lib/hadith/useSideBySide'

import ArabicText from '../ui/ArabicText'
import ErrorAlert from '../ui/ErrorAlert'
import EmptyState from '../ui/EmptyState'
import TopicIcon from '../ui/TopicIcon'
import { AnalyzerSkeleton } from '../ui/Skeleton'
import ReadingOptions from '../ui/ReadingOptions'
import HadithCards from './HadithCards'
import WordsLink from './WordsLink'
import { useHideChain } from '../../lib/hadith/useHideChain'

/** How far down the page you are, drawn into `ref` without re-rendering per scroll. */
function useReadingRail(ref) {
  useEffect(() => {
    const draw = () => {
      const room = document.documentElement.scrollHeight - window.innerHeight
      if (ref.current) ref.current.style.width = `${room > 0 ? Math.min(100, (window.scrollY / room) * 100) : 0}%`
    }
    draw()
    window.addEventListener('scroll', draw, { passive: true })
    return () => window.removeEventListener('scroll', draw)
  }, [ref])
}

export default function HadithList({ collection, book, focus, onBack, accent, onNarrator, onHadith }) {
  const { data, isPending, isError, error, refetch } = useQuery(hadithBookQuery(collection, book))
  useOpenAtTop(collection, book)
  const rail = useRef(null)
  useReadingRail(rail)
  const [missing, setMissing] = useState(false)
  const [columns, setColumns] = useRememberedFlag('hadith-two-columns', false)
  const [sideBySide, setSideBySide] = useSideBySide()
  const [hideChain, setHideChain] = useHideChain()

  // A link to one hadith lands on it, once its book has arrived, and stays there while the cards above fill in.
  useEffect(() => {
    return data && focus ? holdAtTop(document.getElementById(`hadith-${focus}`)) : undefined
  }, [data, focus])

  const jump = (event) => {
    event.preventDefault()
    const number = new FormData(event.currentTarget).get('number')
    const card = number && document.querySelector(`#hadith-${number}, #hadith-${number}a`)
    setMissing(Boolean(number) && !card)
    scrollToEl(card, 'top')
  }

  return (
    <div className="space-y-3">
      <div className="sticky z-[var(--layer-sticky)] top-[var(--app-header-h,0px)] -mx-1 px-1 pt-2 bg-[var(--bg)]">
        <div className="flex items-center gap-3 flex-wrap">
          <button
            type="button"
            onClick={onBack}
            className="press tap type-small text-[var(--text-faint)] hover:text-[var(--text)] transition-colors"
          >
            &larr; Books
          </button>
          {data && (
            <h3 className="flex-1 min-w-[min(100%,14rem)] flex items-start gap-2 type-ui font-medium text-[var(--text)]">
              <TopicIcon topic={topicOf(data.book.name)} className="w-4 h-4 shrink-0 mt-[0.2em]" />
              {/* The name and count as one run of text, the Arabic name under them: as four boxes, a phone
                  split each over two lines. The icon keeps to the first line, the Arabic to the name's start. */}
              <span className="min-w-0">
                {data.book.number}. {data.book.name}
                <span className="ms-2 type-small font-normal text-[var(--text-faint)] whitespace-nowrap">{data.hadiths.length} hadiths</span>
                {data.book.arabic && <ArabicText size="sm" className="block text-left font-normal text-[var(--text-faint)]">{data.book.arabic}</ArabicText>}
              </span>
            </h3>
          )}
          <ReadingOptions accent={accent} options={[
            // A phone has room for one hadith a row, so it is not offered there.
            // Two hadiths a row, each split in two, leaves too little of either: one turns the other off.
            { label: 'Side by side', on: sideBySide && !columns, set: (on) => { setSideBySide(on); if (on) setColumns(false) }, only: 'wide' },
            { label: 'Two columns', on: columns, set: (on) => { setColumns(on); if (on) setSideBySide(false) }, only: 'wide' },
            { label: 'Hide the chain', on: hideChain, set: setHideChain },
          ]} />
          <WordsLink accent={accent} />
          <form onSubmit={jump} className="flex items-center gap-2">
            {missing && <span role="status" className="type-small text-[var(--text-faint)]">Not in this book</span>}
            <input
              name="number"
              type="number"
              min="1"
              inputMode="numeric"
              aria-label="Go to hadith number"
              placeholder="Go to #"
              onChange={() => setMissing(false)}
              className="type-small w-24 h-[var(--layout-chip)] px-3 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text)] outline-none focus:border-[var(--c)]"
              style={{ '--c': accent }}
            />
          </form>
        </div>
        <div className="mt-2 h-0.5 rounded-full bg-[var(--border)]">
          <div ref={rail} style={{ background: accent }} className="h-full w-0 rounded-full" />
        </div>
      </div>

      {isPending && <AnalyzerSkeleton />}

      {isError && (
        <ErrorAlert title="Could not load this book" error={error} fallback="The hadiths could not be reached." onRetry={refetch} />
      )}

      {data && (data.hadiths.length === 0
        ? <EmptyState>This book has no hadiths yet.</EmptyState>
        : <HadithCards items={data.hadiths} collection={collection} accent={accent} columns={columns} onNarrator={onNarrator} onHadith={onHadith} />)}
    </div>
  )
}
