/**
 * Finding an ayah: by its reference, by its Arabic text, or by a root and every
 * place that root occurs.
 *
 * Finding only. What is found opens in QuranReader: an ayah opens its whole
 * surah, scrolled to it, with the ayah studied beside it.
 *
 * The grammar shown there is read from the hand-tagged Quranic Arabic Corpus,
 * not worked out on the fly, so each word's root, case and verb pattern are the
 * ones a scholar assigned. That is also what makes the root links possible: the
 * same root travels to the conjugator and the dictionary.
 */
import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { getQuranRoot, searchQuran } from '../api'
import surahs from '../data/surahs.json'
import { useArrival } from '../lib/useArrival'
import { useHistory } from '../lib/useHistory'
import { isArabic } from '../lib/arabicText'

import QuranSeal from './ui/QuranSeal'
import EmptyState from './ui/EmptyState'
import ErrorAlert from './ui/ErrorAlert'
import RootActions from './ui/RootActions'
import QuranReader from './QuranReader'
import QuranPlacePicker from './QuranPlacePicker'
import QuranSearchBar from './QuranSearchBar'
import SectionHeader from './ui/SectionHeader'
import SourceBadge from './ui/SourceBadge'
import ArabicText from './ui/ArabicText'
import Disclosure from './ui/Disclosure'
import RecentRow from './ui/RecentRow'
import { AnalyzerSkeleton } from './ui/Skeleton'
import { CorrectedNote } from './ui/StatusNote'

// "1:3" as another tab writes it. Anything else arriving is a root.
const AYAH_REF = /^(\d+):(\d+)$/

/** An ayah that is really in the Qur'an, so a mistyped one is never remembered. */
const isAyah = ({ surah, ayah }) => ayah >= 1 && ayah <= (surahs[surah - 1]?.ayahs ?? 0)

export default function QuranLookup({ accent, incoming, arrival, onGo, onVisit }) {
  // What arrived from another tab, if it was an ayah address.
  const address = AYAH_REF.exec(incoming ?? '')
  const arrived = address && { surah: Number(address[1]), ayah: Number(address[2]) }

  // The one box: a place or the words. What it is read as is lib/quranIntent's.
  const [query, setQuery] = useState('')
  // Whether the matches (searched or heard) are on screen: opening an ayah or
  // a surah puts them away.
  const [showMatches, setShowMatches] = useState(false)
  // The ayahs a recitation might have been. Kept apart from the typed search's
  // results because they are a different claim: a search found these words, a
  // recitation was guessed at twice over, once by the listening and once by the
  // matching. Only one of the two lists is ever on screen.
  const [heard, setHeard] = useState(null)
  // The place open in the reader, a surah or an ayah in it, or null for none.
  // The picker follows it too.
  const [at, setAt] = useState(arrived)

  const { history: recent, push: remember } = useHistory('quran-history')

  // An ayah opened is a place reached, written the way every other tab writes
  // one, so the trail and the back arrow can carry it. See lib/journey.js.
  // Only an ayah asked for and really there: one played or scrolled past is not a visit.
  const visit = (place) => {
    if (!isAyah(place)) return
    remember(place)
    onVisit?.(`${place.surah}:${place.ayah}`)
  }
  const search = useMutation({ mutationFn: searchQuran })
  const rootLookup = useMutation({ mutationFn: getQuranRoot })
  // The root behind a single searched word; a 404 just means there is none to show.
  const wordRoot = useMutation({ mutationFn: getQuranRoot })

  // Two different things can arrive and they are told apart by their shape,
  // because they were not before: Daleel hands over an ayah address like "1:3",
  // the Dictionary hands over a root, and every arrival was looked up as a
  // root. An ayah address is not a root, so "Open the ayah" answered "the root
  // does not occur in the Qur'an" for an ayah sitting in the Qur'an.
  const { mutate: lookupRoot } = rootLookup

  // The page follows an arrival during the render. App no longer remounts this
  // panel for one, that remount faded the whole page back in and read as a
  // flash (see lib/useArrival), and what the last arrival left open is not
  // about this one: a surah left open for reading would sit on top of the ayah
  // just asked for, and a list of heard ayahs would sit under it.
  // `arrived` above is the ayah address this word parses into, if any; this is
  // whether it has just come in.
  const { arrived: justCame } = useArrival(arrival)
  if (justCame && incoming) {
    setHeard(null)
    if (arrived) setShowMatches(false)
    setAt(arrived)
  }

  useEffect(() => {
    if (!incoming) return
    if (arrived) visit(arrived)
    else lookupRoot(incoming)
    // `arrived` is derived from `incoming` on every render, so the address
    // itself is the dependency worth naming; `visit` is new every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [arrival, incoming, lookupRoot])
  const runSearch = (text = query.trim()) => {
    setHeard(null)
    if (!text) return
    setShowMatches(true)
    search.mutate(text)
    wordRoot.reset()
    if (!/\s/.test(text) && isArabic(text) && !AYAH_REF.test(text)) wordRoot.mutate(text)
  }

  // What came back from the microphone: the words go in the box so they can be
  // corrected and searched normally, and the ayahs are offered to tap. Shaped
  // like a search result so the same list draws them, rather than a second list
  // that would have to be kept looking like the first one.
  const onHeard = ({ text, ayahs }) => {
    setQuery(text || '')
    search.reset()
    setShowMatches(true)
    setHeard(
      (ayahs || []).map((hit) => ({
        surah: hit.surah,
        ayah: hit.ayah,
        arabic_text: hit.arabic,
        source: { key: 'recitation', label: 'Heard on this machine', confidence: 'guessed' },
      })),
    )
  }
  const readSurah = (n) => { setShowMatches(false); setAt({ surah: n, ayah: null }) }

  const openResult = (place) => {
    setShowMatches(false)
    setAt(place)
    visit(place)
  }
  // The reader moving itself: a surah stepped to, an ayah tapped or shut.
  const onPlace = (place) => (place.ayah ? openResult(place) : setAt(place))

  const busy = search.isPending

  return (
    <div className="panel">
      <QuranSeal wide={Boolean(search.data || at || rootLookup.data)} />
      <SectionHeader title="Quran" arabic="القرآن" />

      <RecentRow
        items={recent.map((h) => `${h.surah}:${h.ayah}`)}
        accent={accent}
        onPick={(item) => {
          const [s, a] = item.split(':')
          openResult({ surah: Number(s), ayah: Number(a) })
        }}
        mono
      />

      <QuranSearchBar
        value={query}
        onChange={setQuery}
        onClear={() => { setQuery(''); setHeard(null); search.reset(); wordRoot.reset() }}
        onOpen={(m, a) => (a === null ? readSurah(m.n) : openResult({ surah: m.n, ayah: a }))}
        onSearch={runSearch}
        onHeard={onHeard}
        busy={busy}
        accent={accent}
      />

      <QuranPlacePicker
        accent={accent}
        surah={at?.surah ?? null}
        ayah={at?.ayah ?? null}
        onReadSurah={readSurah}
        onOpenAyah={(surah, ayah) => openResult({ surah, ayah })}
      />

      {search.isError && (
        // A search that cannot reach Quran.com falls back to the local index
        // and never errors here, so this means the app's own backend did not answer.
        <ErrorAlert
          title="Lookup failed"
          error={search.error}
          fallback="Could not reach the backend. Check that it is running."
          onRetry={() => runSearch()}
        />
      )}

      {rootLookup.isError && (
        <ErrorAlert title="Root not found" error={rootLookup.error} fallback="That root does not occur in the Qur’an." />
      )}
      {rootLookup.data && !rootLookup.isPending && (
        <RootView
          data={rootLookup.data}
          accent={accent}
          onGo={onGo}
          onOpenAyah={openResult}
          onClose={() => rootLookup.reset()}
        />
      )}

      {/* Search matches sit directly under the box, and only until one is
          opened: drawn after the opened ayah they were nine screens down the
          page, and pressing Search looked like it had done nothing. The opened
          ayah stays put underneath, since a new search is not closing it. */}
      {showMatches && (
        heard ? (
          <SearchResults results={heard} onSelect={openResult} accent={accent} />
        ) : search.data ? (
          <div aria-busy={search.isPending} className={`space-y-3 transition-opacity ${search.isPending ? 'opacity-60' : ''}`}>
            <CorrectedNote corrected={search.data.corrected} />
            {wordRoot.data && (
              <RootView data={wordRoot.data} accent={accent} onGo={onGo} onOpenAyah={openResult} folded />
            )}
            <SearchResults results={search.data.hits} onSelect={openResult} accent={accent} />
          </div>
        ) : (
          search.isPending && <AnalyzerSkeleton />
        )
      )}
      {/* Last, so the matches above stay directly under the box. */}
      {at && (
        <QuranReader place={at} accent={accent} onGo={onGo} onPlace={onPlace} onClose={() => setAt(null)} />
      )}
    </div>
  )
}

function SearchResults({ results, onSelect, accent }) {
  if (results.length === 0) {
    return (
      <EmptyState>Nothing matched. Try a shorter phrase, or drop the diacritics.</EmptyState>
    )
  }

  // Which text answered. Search has two: the hand-tagged corpus on this machine
  // and Quran.com over the network, and they are not the same book. One badge
  // per distinct source, so a reader is never left to assume.
  const sources = []
  for (const r of results) {
    if (r.source && !sources.some((s) => s.key === r.source.key)) sources.push(r.source)
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 flex-wrap">
        <p className="text-[var(--text-dim)] type-body">{results.length} matches, pick one to open it</p>
        {sources.map((source) => (
          <SourceBadge key={source.key} source={source} />
        ))}
      </div>
      {results.map((r, i) => (
        <button
          key={`${r.surah}:${r.ayah}`}
          type="button"
          onClick={() => onSelect(r)}
          style={{ '--i': i, '--c': accent }}
          className="rise-in w-full text-left p-4 rounded-[var(--radius-md)]
            bg-[var(--surface)] border border-[var(--border)]
            hover:border-[var(--c)] transition-colors"
        >
          <div className="text-[var(--text-faint)] type-small mb-1 font-mono">{r.surah}:{r.ayah}</div>
          <ArabicText as="div" className="text-right text-[var(--text)]">{r.arabic_text}</ArabicText>
        </button>
      ))}
    </div>
  )
}

// `folded` shuts everything under the "appears N times" line, for a root that
// comes along with a word search rather than being the thing asked for.
function RootView({ data, accent, onGo, onOpenAyah, onClose, folded = false }) {
  const shown = data.occurrences.length

  const title = (
    <div className="flex items-baseline gap-3 flex-wrap">
      <ArabicText size="lg" className="text-[var(--text)]">{data.root}</ArabicText>
      <span className="type-body text-[var(--text-dim)]">
        appears <strong className="text-[var(--text)] tabular-nums">{data.total}</strong> times in the Qur&rsquo;an
      </span>
    </div>
  )

  const body = (
    <div className="space-y-4">
      {folded ? (
        <SourceBadge source={data.source} />
      ) : (
        <div className="flex items-center justify-between gap-3 flex-wrap">
          {title}
          <div className="flex items-center gap-2">
            <SourceBadge source={data.source} />
            <button
              type="button"
              onClick={onClose}
              className="type-small text-[var(--text-faint)] hover:text-[var(--text)] underline underline-offset-2"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {data.forms.length > 0 && (
        <div className="space-y-1.5">
          <p className="type-small text-[var(--text-faint)]">Words built from it, commonest first</p>
          <div className="flex flex-wrap gap-1.5">
            {data.forms.map((f) => (
              <span
                key={`${f.lemma}-${f.pos}`}
                className="flex items-center gap-1.5 type-small px-2.5 py-1 rounded-full
                  bg-[var(--surface)] border border-[var(--border)]"
              >
                <ArabicText className="text-[var(--text)]">{f.lemma}</ArabicText>
                <span className="text-[var(--text-faint)] tabular-nums">{f.uses}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      <RootActions root={data.root} onGo={onGo} exclude="quran" />

      <div className="space-y-1.5">
        {/* Say plainly when the list is cut short, rather than letting a capped
            list read as the whole story. */}
        <p className="type-small text-[var(--text-faint)]">
          {shown < data.total
            ? `First ${shown} of ${data.total} places, pick one to open it`
            : `All ${shown} places, pick one to open it`}
        </p>
        <div className="grid gap-1.5">
          {data.occurrences.map((o, i) => (
            <button
              key={`${o.surah}:${o.ayah}:${i}`}
              type="button"
              onClick={() => onOpenAyah(o)}
              style={{ '--c': accent }}
              className="flex items-center justify-between gap-2 text-left px-3 py-2
                rounded-[var(--radius-md)] bg-[var(--surface)] border border-[var(--border)]
                hover:border-[var(--c)] transition-colors"
            >
              <ArabicText className="text-[var(--text)]">{o.arabic}</ArabicText>
              <span className="type-tiny text-[var(--text-faint)] font-mono shrink-0">
                {o.surah}:{o.ayah}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )

  return folded ? (
    <Disclosure label={title} className="rise-in">{body}</Disclosure>
  ) : (
    <div className="rise-in">{body}</div>
  )
}
