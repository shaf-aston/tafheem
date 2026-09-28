/**
 * The search box on top of Browse. While a search is showing, its hits take
 * the place of `children` (the book list); clearing the box brings the books back.
 *
 * The same box Daleel and the Qur'an tab use, down to the microphone.
 */
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { searchHadith } from '../api'
import { smartError } from '../lib/apiError'
import { useHistory } from '../lib/useHistory'
import { useHadithFavorites } from '../lib/useHadithFavorites'

import ErrorAlert from './ui/ErrorAlert'
import RetryButton from './ui/RetryButton'
import EmptyState from './ui/EmptyState'
import FavoriteStar from './ui/FavoriteStar'
import MicButton from './ui/MicButton'
import RecentRow from './ui/RecentRow'
import SearchBox from './ui/SearchBox'
import { AnalyzerSkeleton } from './ui/Skeleton'
import HadithText from './ui/HadithText'

export default function HadithSearchResults({ collections, accent, children }) {
  const [query, setQuery] = useState('')
  const { history, push: remember } = useHistory('hadith-history')
  const { isFavorite, toggle } = useHadithFavorites()

  const mutation = useMutation({
    mutationFn: searchHadith,
    onSuccess: (_, { q }) => remember({ q }),
  })

  const submit = (overrideQuery) => {
    const q = (overrideQuery ?? query).trim()
    if (!q) return
    mutation.mutate({ q })
  }

  const nameOf = (id) => collections.find((c) => c.id === id)?.name ?? id
  const data = mutation.data
  const searching = mutation.isPending || mutation.isError || Boolean(data)

  return (
    <div className="space-y-3">

      <SearchBox
        id="hadith-search-input"
        label="Search the hadiths"
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
        <ErrorAlert title="Search failed">
          {smartError(mutation.error, 'Could not reach the backend.')}
          <RetryButton onClick={() => submit()} />
        </ErrorAlert>
      )}

      {/* Not an EmptyState: an unbuilt index is not a search that found nothing. */}
      {data?.ready === false && (
        <ErrorAlert title="Search index not built">
          Every search would come back empty until it is built:{' '}
          <code className="px-1 rounded bg-[var(--surface-hi)] text-[var(--text)]">
            python backend/scripts/build_hadith_index.py
          </code>
        </ErrorAlert>
      )}

      {mutation.isPending && <AnalyzerSkeleton />}

      {data?.ready !== false && data && data.hits.length === 0 && (
        <EmptyState>Nothing matches &ldquo;{data.query}&rdquo;.</EmptyState>
      )}

      {data && data.hits.length > 0 && (
        <ul className="list-none m-0 p-0 space-y-2">
          {data.hits.map((h) => (
            <HadithText
              key={`${h.collection}:${h.number}${h.part}`}
              label={`${nameOf(h.collection)} ${h.number}${h.part}`}
              arabic={h.arabic}
              english={h.english}
              accent={accent}
              action={<FavoriteStar on={isFavorite(h)} onClick={() => toggle(h)} />}
            />
          ))}
        </ul>
      )}
    </div>
  )
}
