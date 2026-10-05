/**
 * The search box on top of Browse. While a search is showing, its hits take
 * the place of `children` (the book list); clearing the box brings the books back.
 *
 * The same box Daleel and the Qur'an tab use, down to the microphone.
 *
 * A loose question gets three honest answers around the hits: which typed
 * words were swapped for the nearest word a hadith holds, which matched
 * nothing at all, and the chapters the hits fall in, each a tap away
 * (`onOpenBook`) for narrowing by topic instead of retyping.
 */
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { searchHadith } from '../api'
import { useHistory } from '../lib/useHistory'

import ArabicText from './ui/ArabicText'
import Chip from './ui/Chip'
import ErrorAlert from './ui/ErrorAlert'
import EmptyState from './ui/EmptyState'
import MicButton from './ui/MicButton'
import RecentRow from './ui/RecentRow'
import SearchBox from './ui/SearchBox'
import { AnalyzerSkeleton } from './ui/Skeleton'
import HadithCards from './HadithCards'
import Code from './ui/Code'

export default function HadithSearchResults({ collections, accent, onOpenBook, children }) {
  const [query, setQuery] = useState('')
  const { history, push: remember } = useHistory('hadith-history')

  const mutation = useMutation({
    mutationFn: searchHadith,
    onSuccess: (_, { q }) => remember({ q }),
  })

  const submit = (overrideQuery) => {
    const q = (overrideQuery ?? query).trim()
    if (!q) return
    mutation.mutate({ q })
  }

  const data = mutation.data
  const searching = mutation.isPending || mutation.isError || Boolean(data)

  return (
    <div className="space-y-3">

      <SearchBox
        id="hadith-search-input"
        label="Arabic or English"
        placeholder="patience, الصبر…"
        value={query}
        onChange={setQuery}
        onSubmit={() => submit()}
        onClear={() => { setQuery(''); mutation.reset() }}
        busy={mutation.isPending}
        accent={accent}
      >
        <MicButton
          onHeard={({ text }) => { setQuery(text); submit(text) }}
          accent={accent}
          title="Say what you are looking for"
        />
      </SearchBox>

      {!searching && <RecentRow items={history.map((h) => h.q)} accent={accent} onPick={(q) => { setQuery(q); submit(q) }} />}

      {!searching && children}

      {mutation.isError && (
        <ErrorAlert title="Search failed" error={mutation.error} fallback="Could not reach the backend." onRetry={() => submit()} />
      )}

      {/* Not an EmptyState: an unbuilt index is not a search that found nothing. */}
      {data?.ready === false && (
        <ErrorAlert title="Search index not built">
          Every search would come back empty until it is built:{' '}
          <Code>
            python backend/scripts/build_hadith_index.py
          </Code>
        </ErrorAlert>
      )}

      {mutation.isPending && <AnalyzerSkeleton />}

      {data?.corrected?.length > 0 && (
        <p role="status" className="type-small text-[var(--text-dim)]">
          {data.corrected.map(({ typed, used }, i) => (
            <span key={typed}>
              {i > 0 && ', '}
              searched <Word text={used} /> for <Word text={typed} />
            </span>
          ))}
        </p>
      )}

      {data?.reference && data.reference.asked !== data.reference.shown && (
        <p role="status" className="type-small text-[var(--text-dim)]">
          {collections.find((x) => x.id === data.reference.collection)?.name || data.reference.collection} has
          no {data.reference.asked}, so this is {data.reference.shown}, the nearest number
        </p>
      )}

      {data?.unmatched?.length > 0 && (
        <p role="status" className="type-small text-[var(--text-dim)]">
          no hadith has {data.unmatched.map((w, i) => <span key={w}>{i > 0 && ', '}<Word text={w} /></span>)}
        </p>
      )}

      {data?.partial && (
        <p role="status" className="type-small text-[var(--text-dim)]">no hadith has every word, so these are the closest</p>
      )}

      {data?.ready !== false && data && data.hits.length === 0 && (
        <EmptyState>Nothing matches &ldquo;{data.query}&rdquo;.</EmptyState>
      )}

      {data?.chapters?.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="type-small text-[var(--text-faint)]">Chapters</span>
          {data.chapters.map((c) => (
            <Chip
              key={`${c.collection}:${c.number}`}
              accent={accent}
              tinted
              title={`${c.count} of these hits are in this chapter`}
              onClick={() => { setQuery(''); mutation.reset(); onOpenBook(c.collection, c.number) }}
            >
              {collections.length > 1 && `${collections.find((x) => x.id === c.collection)?.short || c.collection} · `}
              {c.name}
            </Chip>
          ))}
        </div>
      )}

      {data && data.hits.length > 0 && <HadithCards items={data.hits} collections={collections} accent={accent} />}
    </div>
  )
}

// A typed or indexed word, set in its own script.
function Word({ text }) {
  return /[؀-ۿ]/.test(text)
    ? <ArabicText as="span" size="tiny" className="text-[var(--text)]">{text}</ArabicText>
    : <span className="text-[var(--text)]">{text}</span>
}
