/**
 * Hadith: browse a collection by book, or search across it.
 *
 * Same shape as TimelinesPanel and DaleelPanel: fetch the small fixed list
 * once (the collections), own where the tab is (lib/hadithPlace, the same
 * "adjusted during render" pattern TimelinesPanel follows for its own place),
 * and hand the actual work to small named components that read from there.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getHadithCollections } from '../api'
import { smartError } from '../lib/apiError'
import { parsePlace, placeOf } from '../lib/hadithPlace'
import { useHadithFavorites } from '../lib/useHadithFavorites'

import Chip from './ui/Chip'
import EmptyState from './ui/EmptyState'
import SectionHeader from './ui/SectionHeader'
import ErrorAlert from './ui/ErrorAlert'
import RetryButton from './ui/RetryButton'
import { AnalyzerSkeleton } from './ui/Skeleton'
import HadithCollectionPicker from './HadithCollectionPicker'
import HadithBookList from './HadithBookList'
import HadithCards from './HadithCards'
import HadithList from './HadithList'
import HadithSearchResults from './HadithSearchResults'

export default function HadithPanel({ accent, incoming, arrival, onVisit }) {
  const { data: collections, isPending, isError, error, refetch } = useQuery({
    queryKey: ['hadith-collections'],
    queryFn: getHadithCollections,
    staleTime: Infinity,
  })
  const [place, setPlace] = useState(null)   // { collection, book, number, part }
  const [starred, setStarred] = useState(false)
  const { favorites } = useHadithFavorites()

  // A deep link, a link from another tab, or the back arrow landing here: all
  // three read the same way, once per arrival. See TimelinesPanel for why
  // this is adjusted during render rather than in an effect.
  const [seenLink, setSeenLink] = useState(null)
  const [missed, setMissed] = useState(false)
  const link = `${arrival}:${incoming}`
  if (collections && link !== seenLink) {
    setSeenLink(link)
    const asked = parsePlace(incoming, collections)
    if (asked) setPlace(asked)
    else if (collections.length) setPlace({ collection: collections[0].id, book: null, number: null, part: '' })
    setMissed(Boolean(incoming) && !asked)
  }

  if (isPending) return <AnalyzerSkeleton />

  if (isError) {
    return (
      <ErrorAlert title="Could not load the hadith collections">
        {smartError(error, 'The hadith collections could not be reached.')}
        <RetryButton onClick={refetch} />
      </ErrorAlert>
    )
  }

  if (!collections.length) {
    return (
      <div className="space-y-3">
        <SectionHeader title="Hadith" arabic="الحديث" />
        <ErrorAlert title="No collection is built yet">
          Fetch and build one with{' '}
          <code className="px-1 rounded bg-[var(--surface-hi)] text-[var(--text)]">
            python backend/scripts/fetch_hadith_collections.py
          </code>{' '}
          then{' '}
          <code className="px-1 rounded bg-[var(--surface-hi)] text-[var(--text)]">
            python backend/scripts/build_hadith_index.py
          </code>
        </ErrorAlert>
      </div>
    )
  }

  const collection = collections.some((c) => c.id === place?.collection) ? place.collection : collections[0].id

  const go = (next) => {
    setMissed(false)
    setStarred(false)
    setPlace(next)
    onVisit?.(placeOf(next.collection, next.book, next.number, next.part))
  }
  const pickCollection = (id) => go({ collection: id, book: null, number: null, part: '' })
  const pickBook = (number) => go({ collection, book: number, number: null, part: '' })
  const backToBooks = () => go({ collection, book: null, number: null, part: '' })

  return (
    <div className="space-y-3">
      <SectionHeader title="Hadith" arabic="الحديث" />

      {missed && (
        <p role="status" className="type-small text-[var(--text-dim)]">
          That link names a hadith that is not here, so the collection opens plainly.
        </p>
      )}

      <HadithSearchResults collections={collections} accent={accent}>
        <div className="flex items-center gap-2 flex-wrap">
          <HadithCollectionPicker collections={collections} value={collection} onChange={pickCollection} accent={accent} />
          <Chip selected={starred} tinted accent={accent} onClick={() => setStarred(!starred)}>
            &#9733; Starred {favorites.length > 0 && favorites.length}
          </Chip>
        </div>
        {starred ? (
          favorites.length
            ? <HadithCards items={favorites} collections={collections} accent={accent} />
            : <EmptyState>Star a hadith and it is kept here.</EmptyState>
        ) : place?.book == null ? (
          <HadithBookList collection={collection} onPick={pickBook} accent={accent} />
        ) : (
          <HadithList collection={collection} book={place.book} onBack={backToBooks} accent={accent} />
        )}
      </HadithSearchResults>
    </div>
  )
}
