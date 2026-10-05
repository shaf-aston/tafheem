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
 * retyping. A search that only names a collection ("bukhari") opens it.
 */
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { searchHadith } from '../api'
import { useHadithCollections } from '../lib/useHadithCollections'
import { useHistory } from '../lib/useHistory'

import ArabicText from './ui/ArabicText'
import Chip from './ui/Chip'
import ChipRow from './ui/ChipRow'
import ErrorAlert from './ui/ErrorAlert'
import EmptyState from './ui/EmptyState'
import IndexNotBuilt from './ui/IndexNotBuilt'
import MicButton from './ui/MicButton'
import RecentRow from './ui/RecentRow'
import SearchBox from './ui/SearchBox'
import { AnalyzerSkeleton } from './ui/Skeleton'
import StatusNote from './ui/StatusNote'
import HadithCards from './HadithCards'

export default function HadithSearchResults({ accent, onOpenBook, children }) {
  const [query, setQuery] = useState('')
  const { collections, of } = useHadithCollections()
  const { history, push: remember } = useHistory('hadith-history')

  const mutation = useMutation({
    mutationFn: searchHadith,
    onSuccess: (_, { q }) => remember({ q }),
  })

  const open = (collection, book) => {
    setQuery('')
    mutation.reset()
    onOpenBook(collection, book)
  }

  const submit = (overrideQuery) => {
    const q = (overrideQuery ?? query).trim()
    if (!q) return
    mutation.mutate({ q }, {
      onSuccess: ({ reference }) => { if (reference && !reference.asked) open(reference.collection, null) },
    })
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

      {data?.ready === false && <IndexNotBuilt command="python backend/scripts/build_hadith_index.py" />}

      {mutation.isPending && <AnalyzerSkeleton />}

      {data?.collections?.length > 0 && !data.reference && (
        <StatusNote>searched only {data.collections.map((id) => of(id).name).join(' and ')}</StatusNote>
      )}

      {data?.corrected?.length > 0 && (
        <StatusNote>
          {data.corrected.map(({ typed, used }, i) => (
            <span key={typed}>
              {i > 0 && ', '}
              searched <Word text={used} /> for <Word text={typed} />
            </span>
          ))}
        </StatusNote>
      )}

      {data?.reference && data.reference.asked !== data.reference.shown && (
        <StatusNote>
          {of(data.reference.collection).name} has
          no {data.reference.asked}, so this is {data.reference.shown}, the nearest number
        </StatusNote>
      )}

      {data?.unmatched?.length > 0 && (
        <StatusNote>
          no hadith has {data.unmatched.map((w, i) => <span key={w}>{i > 0 && ', '}<Word text={w} /></span>)}
        </StatusNote>
      )}

      {data?.partial && <StatusNote>no hadith has every word, so these are the closest</StatusNote>}

      {data?.ready !== false && data && data.hits.length === 0 && (
        <EmptyState>Nothing matches &ldquo;{data.query}&rdquo;.</EmptyState>
      )}

      {data?.chapters?.length > 0 && (
        <ChipRow label="Chapters">
          {data.chapters.map((c) => (
            <Chip
              key={`${c.collection}:${c.number}`}
              accent={accent}
              quiet
              title={`${c.count} of these hits are in this chapter`}
              onClick={() => open(c.collection, c.number)}
            >
              {collections.length > 1 && `${of(c.collection).short} · `}
              {c.name}
            </Chip>
          ))}
        </ChipRow>
      )}

      {data && data.hits.length > 0 && <HadithCards items={data.hits} accent={accent} />}
    </div>
  )
}

// A typed or indexed word, set in its own script.
function Word({ text }) {
  return /[؀-ۿ]/.test(text)
    ? <ArabicText as="span" size="tiny" className="text-[var(--text)]">{text}</ArabicText>
    : <span className="text-[var(--text)]">{text}</span>
}
