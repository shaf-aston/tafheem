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

import { hadithCollectionsQuery } from '../api'
import { parsePlace, placeOf } from '../lib/hadithPlace'
import { useHadithFavorites } from '../lib/useHadithFavorites'

import Chip from './ui/Chip'
import EmptyState from './ui/EmptyState'
import SectionHeader from './ui/SectionHeader'
import ErrorAlert from './ui/ErrorAlert'
import { AnalyzerSkeleton } from './ui/Skeleton'
import HadithCollectionPicker from './HadithCollectionPicker'
import HadithBookList from './HadithBookList'
import HadithCards from './HadithCards'
import HadithList from './HadithList'
import HadithSearchResults from './HadithSearchResults'
import Code from './ui/Code'

export default function HadithPanel({ accent, incoming, arrival, onVisit }) {
  const { data: collections, isPending, isError, error, refetch } = useQuery(hadithCollectionsQuery)
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
      <ErrorAlert title="Could not load the hadith collections" error={error} fallback="The hadith collections could not be reached." onRetry={refetch} />
    )
  }

  if (!collections.length) {
    return (
      <div className="panel">
        <SectionHeader title="Hadith" arabic="الحديث" subtitle="Search and read the hadith collections." />
        <ErrorAlert title="No collection is built yet">
          Fetch and build one with{' '}
          <Code>
            python backend/scripts/fetch_hadith_collections.py
          </Code>{' '}
          then{' '}
          <Code>
            python backend/scripts/build_hadith_index.py
          </Code>
        </ErrorAlert>
      </div>
    )
  }

  const open = collections.find((c) => c.id === place?.collection) ?? collections[0]
  const collection = open.id

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
    <div className="panel">
      <SectionHeader title="Hadith" arabic="الحديث" subtitle="Search and read the hadith collections." />

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
        {!starred && (
          <p className="type-small text-[var(--text-faint)] flex items-center gap-2">
            {open.name}
            {open.sahih && (
              <>
                <span aria-hidden="true" className="inline-block w-1.5 h-1.5 rounded-full bg-[var(--success)]" />
                every hadith in it is graded sahih
              </>
            )}
          </p>
        )}
        {starred ? (
          favorites.length
            ? <HadithCards items={favorites} collections={collections} accent={accent} />
            : <EmptyState>Star a hadith and it is kept here.</EmptyState>
        ) : place?.book == null ? (
          <HadithBookList collection={collection} onPick={pickBook} accent={accent} />
        ) : (
          <HadithList collection={collection} collections={collections} book={place.book} onBack={backToBooks} accent={accent} />
        )}
      </HadithSearchResults>
    </div>
  )
}
