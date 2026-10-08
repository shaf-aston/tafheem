/**
 * Hadith: browse a collection by book, or search across it.
 *
 * Same shape as TimelinesPanel and DaleelPanel: fetch the small fixed list
 * once (the collections), own where the tab is (lib/hadithPlace, the same
 * "adjusted during render" pattern TimelinesPanel follows for its own place),
 * and hand the actual work to small named components that read from there.
 */
import { useEffect, useState } from 'react'
import { useArrivalWhenReady } from '../lib/useArrival'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { hadithBookQuery, hadithCollectionsQuery } from '../api'
import { bookOf, listOf, NARRATORS_PLACE, narratorOf, narratorPlaceOf, parsePlace, placeOf, SCHOLARS_PLACE } from '../lib/hadithPlace'
import { useHadithFavorites } from '../lib/useHadithFavorites'

import Chip from './ui/Chip'
import ChipRow from './ui/ChipRow'
import EmptyState from './ui/EmptyState'
import SectionHeader from './ui/SectionHeader'
import ErrorAlert from './ui/ErrorAlert'
import { AnalyzerSkeleton } from './ui/Skeleton'
import StatusNote from './ui/StatusNote'
import HadithCollectionPicker from './HadithCollectionPicker'
import HadithBookList from './HadithBookList'
import HadithCards from './HadithCards'
import HadithList from './HadithList'
import HadithSearchResults from './HadithSearchResults'
import NarratorList from './NarratorList'
import NarratorPage from './NarratorPage'
import ScholarTerms from './ScholarTerms'
import Code from './ui/Code'
import SourceBadge from './ui/SourceBadge'
import { useSources } from '../lib/useSources'

export default function HadithPanel({ accent, incoming, arrival, onVisit, onGo }) {
  const { data: collections, isPending, isError, error, refetch } = useQuery(hadithCollectionsQuery)
  const [place, setPlace] = useState(null)   // { collection, book, number, part }
  const [narrator, setNarrator] = useState(null)   // the narrator whose page is open, if any
  const [starred, setStarred] = useState(false)
  const [listing, setListing] = useState(null)   // the list showing, narrators or scholars, if any
  const { favorites } = useHadithFavorites()
  const source = useSources().sources.find((s) => s.key === 'hadith')

  // A link naming a book starts that book loading beside the collections, not after them.
  const client = useQueryClient()
  useEffect(() => {
    const named = bookOf(incoming)
    if (named) client.prefetchQuery(hadithBookQuery(...named))
  }, [client, incoming])

  // A deep link, a link from another tab, or the back arrow landing here: all
  // three read the same way, once per arrival (see lib/useArrival).
  const [missed, setMissed] = useState(false)
  if (useArrivalWhenReady(arrival, Boolean(collections))) {
    const asked = parsePlace(incoming, collections)
    setNarrator(narratorOf(incoming))
    setListing(listOf(incoming))
    if (asked) setPlace(asked)
    else if (collections.length) setPlace({ collection: collections[0].id, book: null, number: null, part: '' })
    setMissed(Boolean(incoming) && !asked && !narratorOf(incoming) && !listOf(incoming))
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
        <SectionHeader title="Hadith" arabic="الحديث" />
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
    setListing(null)
    setNarrator(null)
    setPlace(next)
    onVisit?.(placeOf(next.collection, next.book, next.number, next.part))
  }
  // A narrator's page is a step of its own, so Back returns to where he was tapped.
  const openHadith = (h) => go({ collection: h.collection, book: h.book, number: h.number, part: h.part })
  const openNarrator = (id) => onGo('hadith', narratorPlaceOf(id))
  const pickCollection = (id) => go({ collection: id, book: null, number: null, part: '' })
  const pickBook = (number) => go({ collection, book: number, number: null, part: '' })
  const backToBooks = () => go({ collection, book: null, number: null, part: '' })

  if (narrator != null) {
    return (
      <div className="panel">
        <SectionHeader title="Hadith" arabic="الحديث" />
        <NarratorPage
          id={narrator}
          accent={accent}
          onNarrator={openNarrator}
          onHadith={openHadith}
        />
      </div>
    )
  }

  return (
    <div className="panel">
      <SectionHeader title="Hadith" arabic="الحديث" />

      {missed && (
        <StatusNote>That link names a hadith that is not here, so the collection opens plainly.</StatusNote>
      )}

      <HadithSearchResults accent={accent} onNarrator={openNarrator} onHadith={openHadith} onOpenBook={(id, number) => go({ collection: id, book: number, number: null, part: '' })}>
        <ChipRow>
          <HadithCollectionPicker value={collection} onChange={pickCollection} accent={accent} />
          <Chip selected={starred} tinted accent={accent} onClick={() => setStarred(!starred)}>
            &#9733; Starred {favorites.length > 0 && favorites.length}
          </Chip>
          <Chip selected={listing === NARRATORS_PLACE} tinted accent={accent} onClick={() => (listing === NARRATORS_PLACE ? go(place) : onGo('hadith', NARRATORS_PLACE))}>
            Narrators
          </Chip>
          <Chip selected={listing === SCHOLARS_PLACE} tinted accent={accent} onClick={() => (listing === SCHOLARS_PLACE ? go(place) : onGo('hadith', SCHOLARS_PLACE))}>
            Scholars
          </Chip>
          {/* The dictionary's badge: the dot is how far the text can be trusted, the label is this
              collection, unless the picker beside it already names it. */}
          {!starred && !listing && source && <SourceBadge source={collections.length > 1 ? source : { ...source, label: open.name }} className="ml-auto" />}
        </ChipRow>
        {listing === NARRATORS_PLACE ? (
          <NarratorList accent={accent} onOpen={openNarrator} />
        ) : listing === SCHOLARS_PLACE ? (
          <ScholarTerms accent={accent} onOpen={openHadith} />
        ) : starred ? (
          favorites.length
            ? <HadithCards items={favorites} accent={accent} onNarrator={openNarrator} onHadith={openHadith} />
            : <EmptyState>Star a hadith and it is kept here.</EmptyState>
        ) : place?.book == null ? (
          <HadithBookList collection={collection} onPick={pickBook} accent={accent} />
        ) : (
          <HadithList collection={collection} book={place.book} focus={place.number != null ? `${place.number}${place.part}` : null} onBack={backToBooks} accent={accent} onNarrator={openNarrator} onHadith={openHadith} />
        )}
      </HadithSearchResults>
    </div>
  )
}
