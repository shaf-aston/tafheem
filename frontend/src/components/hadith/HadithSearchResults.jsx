/**
 * The search box on top of Browse. While a search is showing, its hits take
 * the place of `children` (the book list); clearing the box brings the books back.
 *
 * The same box Daleel and the Qur'an tab use, down to the microphone.
 *
 * A loose question gets honest answers around the hits: which typed words
 * were swapped for the nearest word a hadith holds, which matched nothing at
 * all, which collection a name in it narrowed to, and the chapters the hits
 * fall in, each a tap away (`onOpenBook`) for narrowing by topic instead of
 * retyping. Narrators whose name starts with the words typed sit above the hits,
 * each a tap to his page. A search that only names a collection ("bukhari") opens it.
 * `places` (the PlaceStrip) stands under the box, always in view. While a search is showing, "← Books", the ✕ and Esc
 * all clear it and bring the books back.
 */
import { useEffect, useEffectEvent } from 'react'

import { searchHadith } from '../../api'
import { useHadithCollections } from '../../lib/hadith/useHadithCollections'
import { useNarratorMatches } from '../../lib/hadith/useNarrators'
import { useSearch } from '../../lib/hooks/useSearch'

import Chip from '../ui/inputs/Chip'
import ChipRow from '../ui/inputs/ChipRow'
import CloseButton from '../ui/buttons/CloseButton'
import ErrorAlert from '../ui/feedback/ErrorAlert'
import EmptyState from '../ui/feedback/EmptyState'
import IndexNotBuilt from '../ui/feedback/IndexNotBuilt'
import MicButton from '../ui/buttons/MicButton'
import { NarratorLinks } from './NarratorParts'
import RecentRow from '../ui/inputs/RecentRow'
import SearchBox from '../ui/inputs/SearchBox'
import ShowRest from '../ui/buttons/ShowRest'
import { AnalyzerSkeleton } from '../ui/feedback/Skeleton'
import StatusNote, { CorrectedNote, NoteWord } from '../ui/feedback/StatusNote'
import HadithCards from './HadithCards'
import HadithOptions from './HadithOptions'

export default function HadithSearchResults({ accent, onOpenBook, onNarrator, onHadith, places, children }) {
  const { collections, of } = useHadithCollections()
  const { query, setQuery, history, mutation, submit, clear, shown: data } = useSearch({
    historyKey: 'hadith-history',
    ask: searchHadith,
    onVisit: (_, { reference }) => { if (reference && !reference.asked) open(reference.collection, null) },
  })

  const narrators = useNarratorMatches(data?.query)

  const open = (collection, book) => {
    clear()
    onOpenBook(collection, book)
  }

  const searching = mutation.isPending || mutation.isError || Boolean(data)

  // Esc leaves the results for the books, unless a sheet is open: Esc closes that first.
  const leave = useEffectEvent((event) => {
    if (event.key === 'Escape' && !document.querySelector('dialog[open]')) clear()
  })
  useEffect(() => {
    if (!searching) return undefined
    document.addEventListener('keydown', leave)
    return () => document.removeEventListener('keydown', leave)
  }, [searching])

  return (
    <div className="space-y-3">

      <SearchBox
        id="hadith-search-input"
        label="Arabic or English"
        verb="search"
        placeholder="patience, الصبر…"
        value={query}
        onChange={setQuery}
        onSubmit={submit}
        onClear={clear}
        busy={mutation.isPending}
        accent={accent}
      >
        <MicButton
          onHeard={({ text }) => submit(text)}
          accent={accent}
          title="Say what you are looking for"
        />
      </SearchBox>

      {places}

      {searching && (
        <div className="flex items-center gap-3">
          <button type="button" onClick={clear} className="press tap type-small text-[var(--text-faint)] hover:text-[var(--text)] transition-colors">
            &larr; Books
          </button>
          <p className="flex-1 min-w-0 truncate type-small text-[var(--text-dim)] m-0">
            {data ? <>Results for &ldquo;{data.query}&rdquo;</> : 'Searching…'}
          </p>
          <CloseButton onClick={clear} aria-label="Close search" className="shrink-0" />
        </div>
      )}

      {!searching && <RecentRow items={history.map((h) => h.q)} accent={accent} onPick={submit} />}

      {!searching && children}

      {mutation.isError && (
        <ErrorAlert title="Search failed" error={mutation.error} fallback="Could not reach the backend." onRetry={() => submit()} />
      )}

      {data?.ready === false && <IndexNotBuilt command="python backend/scripts/hadith/build_hadith_index.py" />}

      {mutation.isPending && <AnalyzerSkeleton />}

      {data?.collections?.length > 0 && !data.reference && (
        <StatusNote>searched only {data.collections.map((id) => of(id).name).join(' and ')}</StatusNote>
      )}

      <CorrectedNote corrected={data?.corrected} />

      {data?.reference && data.reference.asked !== data.reference.shown && (
        <StatusNote>
          {of(data.reference.collection).name} has
          no {data.reference.asked}, so this is {data.reference.shown}, the nearest number
        </StatusNote>
      )}

      {data?.unmatched?.length > 0 && (
        <StatusNote>
          no hadith has {data.unmatched.map((w, i) => <span key={w}>{i > 0 && ', '}<NoteWord text={w} /></span>)}
        </StatusNote>
      )}

      {data?.partial && <StatusNote>no hadith has every word, so these are the closest</StatusNote>}

      {data?.ready !== false && data && data.hits.length === 0 && (
        <EmptyState>Nothing matches &ldquo;{data.query}&rdquo;.</EmptyState>
      )}

      {narrators.length > 0 && (
        <div className="space-y-1.5">
          <span className="type-small text-[var(--text-faint)]">Narrators</span>
          <ShowRest lines={4} accent={accent} more={`Show all ${narrators.length}`}>
            <NarratorLinks items={narrators} onOpen={onNarrator} row />
          </ShowRest>
        </div>
      )}

      {data?.chapters?.length > 0 && (
        <ChipRow label="Chapters">
          {data.chapters.map((c) => (
            <Chip
              key={`${c.collection}:${c.number}`}
              accent={accent}
              quiet
              title={`${c.name}: ${c.count} of these hits are in this chapter`}
              onClick={() => open(c.collection, c.number)}
            >
              {collections.length > 1 && `${of(c.collection).short} · `}
              {c.name}
            </Chip>
          ))}
        </ChipRow>
      )}

      {data && data.hits.length > 0 && (
        <>
          <HadithOptions accent={accent} />
          <HadithCards items={data.hits} accent={accent} onNarrator={onNarrator} onHadith={onHadith} />
        </>
      )}
    </div>
  )
}
