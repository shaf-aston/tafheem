/**
 * One book's hadiths in full. The title bar stays under the app header while
 * you read: the way back, how far through you are, a jump to a number, and a
 * quiet icon that opens how the hadiths are laid out (two per row, chain hidden).
 */
import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { hadithBookQuery } from '../api'
import { scrollToEl } from '../lib/scrollToEl'
import { topicOf } from '../lib/hadithGrade'
import { useNarrators } from '../lib/useNarrators'
import { useRememberedFlag } from '../lib/useRemembered'

import Chip from './ui/Chip'
import ChipRow from './ui/ChipRow'
import ErrorAlert from './ui/ErrorAlert'
import EmptyState from './ui/EmptyState'
import TopicIcon from './ui/TopicIcon'
import ChainSheet from './ui/ChainSheet'
import { AnalyzerSkeleton } from './ui/Skeleton'
import HadithCards from './HadithCards'

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

export default function HadithList({ collection, book, focus, onBack, accent, onNarrator }) {
  const { data, isPending, isError, error, refetch } = useQuery(hadithBookQuery(collection, book))
  const names = useNarrators(collection, book)
  const rail = useRef(null)
  useReadingRail(rail)
  const [missing, setMissing] = useState(false)
  const [columns, setColumns] = useRememberedFlag('hadith-two-columns', false)
  const [hideChain, setHideChain] = useRememberedFlag('hadith-hide-chain', false)
  const [guide, setGuide] = useState(false)

  // A link to one hadith lands on it, once its book has arrived.
  useEffect(() => {
    if (data && focus) scrollToEl(document.getElementById(`hadith-${focus}`), 'top')
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
            className="press type-small text-[var(--text-faint)] hover:text-[var(--text)] transition-colors"
          >
            &larr; Books
          </button>
          {data && (
            <h3 className="flex-1 min-w-[min(100%,14rem)] flex items-center gap-2 type-ui font-medium text-[var(--text)]">
              <TopicIcon topic={topicOf(data.book.name)} className="w-4 h-4" />
              {data.book.number}. {data.book.name}
              <span className="ms-2 type-small font-normal text-[var(--text-faint)]">{data.hadiths.length} hadiths</span>
            </h3>
          )}
          <ReadingOptions accent={accent} options={[
            // A phone has room for one hadith a row, so it is not offered there.
            { label: 'Two columns', on: columns, set: setColumns, wide: true },
            { label: 'Hide the chain', on: hideChain, set: setHideChain },
          ]}>
            <Chip tinted accent={accent} onClick={() => setGuide(true)}>Chain words</Chip>
          </ReadingOptions>
          {guide && <ChainSheet accent={accent} onClose={() => setGuide(false)} />}
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
        : <HadithCards items={data.hadiths} collection={collection} accent={accent} columns={columns} hideChain={hideChain} names={names} onNarrator={onNarrator} />)}
    </div>
  )
}

/** A small sliders icon; pressed, its on/off chips (and `children`) slide out beside it in the bar. */
function ReadingOptions({ options, accent, children }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="flex items-center gap-3" style={{ '--c': accent }}>
      {open && (
        <ChipRow className="fade-in">
          {options.map(({ label, on, set, wide }) => (
            <span key={label} className={wide ? 'hidden md:contents' : 'contents'}>
              <Chip tinted selected={on} accent={accent} onClick={() => set(!on)}>{label}</Chip>
            </span>
          ))}
          {children}
        </ChipRow>
      )}
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-label="Reading options"
        title="Reading options"
        className={`press grid place-items-center w-[var(--layout-chip)] h-[var(--layout-chip)] rounded-full transition-colors ${
          open ? 'text-[var(--c)]' : 'text-[var(--text-faint)] hover:text-[var(--text-dim)]'
        }`}
      >
        <svg aria-hidden="true" viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M4 7h10M18 7h2M4 17h4M12 17h8" />
          <circle cx="16" cy="7" r="2" />
          <circle cx="10" cy="17" r="2" />
        </svg>
      </button>
    </div>
  )
}
