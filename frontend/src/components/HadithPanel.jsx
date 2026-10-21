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
import { useQueries, useQuery, useQueryClient } from '@tanstack/react-query'

import { hadithBookQuery, hadithBooksQuery, hadithCollectionsQuery, narratorQuery, searchHadith } from '../api'
import { bookOf, listOf, nameOfPlace, NARRATORS_PLACE, narratorOf, narratorPlaceOf, parsePlace, placeOf, SCHOLARS_PLACE, shortOf } from '../lib/hadithPlace'
import { useHadithFavorites } from '../lib/useHadithFavorites'
import { nearest, tabNow, trailFor, useJourney } from '../lib/journey'
import { TRAIL_STEPS } from '../lib/session'

import Chip from './ui/Chip'
import ChipRow from './ui/ChipRow'
import EmptyState from './ui/EmptyState'
import SectionHeader from './ui/SectionHeader'
import ErrorAlert from './ui/ErrorAlert'
import { AnalyzerSkeleton } from './ui/Skeleton'
import StatusNote from './ui/StatusNote'
import HadithCollectionPicker from './hadith/HadithCollectionPicker'
import HadithBookList from './hadith/HadithBookList'
import HadithCards from './hadith/HadithCards'
import HadithMoreMenu from './hadith/HadithMoreMenu'
import HadithOptions from './hadith/HadithOptions'
import HadithList from './hadith/HadithList'
import HadithSearchResults from './hadith/HadithSearchResults'
import NarratorList from './hadith/NarratorList'
import NarratorPage from './hadith/NarratorPage'
import ScholarTerms from './hadith/ScholarTerms'
import Code from './ui/Code'
import SourceBadge from './ui/SourceBadge'
import { useSources } from '../lib/useSources'

const noop = () => {}

export default function HadithPanel({ accent, incoming, arrival, onVisit, onGo }) {
  const { data: collections, isPending, isError, error, refetch } = useQuery(hadithCollectionsQuery)
  const [place, setPlace] = useState(null)   // { collection, book, number, part }
  const [narrator, setNarrator] = useState(null)   // the narrator whose page is open, if any
  const [starred, setStarred] = useState(false)
  const [listing, setListing] = useState(null)   // the list showing, narrators or scholars, if any
  const { favorites } = useHadithFavorites()
  // The trail names each step: "Bukhari 5a", a narrator by his name. Every narrator on the trail is
  // watched (the same request his page makes), so a name lands once it arrives, a reloaded trail too.
  const client = useQueryClient()
  const { steps, at } = useJourney()
  const onTrail = new Set([narrator, ...nearest(trailFor(steps, tabNow(steps, at), at), at, TRAIL_STEPS).shown.map((step) => narratorOf(step.value))])
  onTrail.delete(null)
  const pages = useQueries({ queries: [...onTrail].map((id) => narratorQuery(id)) })
  const names = Object.fromEntries([...onTrail].map((id, n) => [id, pages[n].data?.name_en]))
  const named = (q) => nameOfPlace(q, collections, (id) => names[id])
  const source = useSources().sources.find((s) => s.key === 'hadith')

  // A link naming a book starts that book loading beside the collections, not after them.
  useEffect(() => {
    const named = bookOf(incoming)
    if (named) client.prefetchQuery(hadithBookQuery(...named))
  }, [client, incoming])

  // A link with no book (muslim/2927) is read once its collection's books say the number is no book, and
  // search, which already reads "muslim 2927", has found which book holds it.
  const pair = /^[^/]+\/\d+[a-z]?$/.test(incoming ?? '') && !narratorOf(incoming) ? incoming.split('/') : null
  const books = useQuery({ ...hadithBooksQuery(pair?.[0]), enabled: Boolean(pair) })
  const short = shortOf(incoming, books.data)
  const found = useQuery({
    queryKey: ['hadith-short', incoming],
    queryFn: () => searchHadith({ q: pair.join(' '), collections: [short] }),
    enabled: Boolean(short),
  })
  const hit = found.data?.reference && found.data.reference.asked === found.data.reference.shown ? found.data.hits[0] : null
  const known = !pair || books.isFetched && (!short || found.isFetched)

  // A deep link, a link from another tab, or the back arrow landing here: all
  // three read the same way, once per arrival (see lib/useArrival).
  const [missed, setMissed] = useState(false)
  if (useArrivalWhenReady(arrival, Boolean(collections) && known)) {
    const asked = hit ? { collection: hit.collection, book: hit.book, number: hit.number, part: hit.part } : short ? null : parsePlace(incoming, collections)
    setNarrator(narratorOf(incoming))
    setListing(listOf(incoming))
    if (asked) setPlace(asked)
    else if (collections.length) setPlace({ collection: collections[0].id, book: null, number: null, part: '' })
    setMissed(Boolean(incoming) && !asked && !narratorOf(incoming) && !listOf(incoming))
  }

  // The header and the search box are the loaded page's own, inert until the
  // collections arrive, so only the skeleton below them is replaced.
  if (isPending) {
    return (
      <div className="panel">
        <SectionHeader title="Hadith" arabic="الحديث" emblem="hadith" nameOf={named} />
        <div inert>
          <HadithSearchResults accent={accent} onNarrator={noop} onHadith={noop} onOpenBook={noop}>
            <AnalyzerSkeleton />
          </HadithSearchResults>
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <ErrorAlert title="Could not load the hadith collections" error={error} fallback="The hadith collections could not be reached." onRetry={refetch} />
    )
  }

  if (!collections.length) {
    return (
      <div className="panel">
        <SectionHeader title="Hadith" arabic="الحديث" emblem="hadith" nameOf={named} />
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
        <SectionHeader title="Hadith" arabic="الحديث" emblem="hadith" nameOf={named} />
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
      <SectionHeader title="Hadith" arabic="الحديث" emblem="hadith" nameOf={named} />

      {missed && (
        <StatusNote>That link names a hadith that is not here, so the collection opens plainly.</StatusNote>
      )}

      <HadithSearchResults
        accent={accent}
        onNarrator={openNarrator}
        onHadith={openHadith}
        onOpenBook={(id, number) => go({ collection: id, book: number, number: null, part: '' })}
        menu={(
          <HadithMoreMenu accent={accent} items={[
            { label: '★ Starred', count: favorites.length, on: starred, pick: () => setStarred(!starred) },
            { label: 'Narrators', hint: 'who passed them on', on: listing === NARRATORS_PLACE, pick: () => (listing === NARRATORS_PLACE ? go(place) : onGo('hadith', NARRATORS_PLACE)) },
            { label: 'Scholars', hint: 'what they said of them', on: listing === SCHOLARS_PLACE, pick: () => (listing === SCHOLARS_PLACE ? go(place) : onGo('hadith', SCHOLARS_PLACE)) },
          ]} />
        )}
      >
        <ChipRow>
          <HadithCollectionPicker value={collection} onChange={pickCollection} accent={accent} />
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
            ? (
              <>
                <HadithOptions accent={accent} />
                <HadithCards items={favorites} accent={accent} onNarrator={openNarrator} onHadith={openHadith} />
              </>
            )
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
