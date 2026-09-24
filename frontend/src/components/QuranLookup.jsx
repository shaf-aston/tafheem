/**
 * Finding an ayah: by its reference, by its Arabic text, or by a root and every
 * place that root occurs.
 *
 * Finding only. What one ayah then says, word by word, is AyahStudy's job, and
 * this hands the found ayah straight to it.
 *
 * The grammar shown there is read from the hand-tagged Quranic Arabic Corpus,
 * not worked out on the fly, so each word's root, case and verb pattern are the
 * ones a scholar assigned. That is also what makes the root links possible: the
 * same root travels to the conjugator and the dictionary.
 */
import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { getQuranAyah, getQuranRoot, searchQuran } from '../api'
import { hasDiacritics } from '../lib/arabicText'
import { smartError } from '../lib/apiError'
import { useArrival } from '../lib/useArrival'
import { useHistory } from '../lib/useHistory'

import AyahStudy from './AyahStudy'
import EmptyState from './ui/EmptyState'
import ErrorAlert from './ui/ErrorAlert'
import PrimaryButton from './ui/PrimaryButton'
import RetryButton from './ui/RetryButton'
import RootActions from './ui/RootActions'
import SurahReader from './SurahReader'
import SurahRefBox from './SurahRefBox'
import MicButton from './ui/MicButton'
import SectionHeader from './ui/SectionHeader'
import SourceBadge from './ui/SourceBadge'
import ArabicText from './ui/ArabicText'
import SearchBox from './ui/SearchBox'
import RecentRow from './ui/RecentRow'
import { AnalyzerSkeleton } from './ui/Skeleton'

const MODES = [
  { id: 'ref', label: 'Surah & ayah' },
  { id: 'search', label: 'Arabic text' },
]

// "1:3" as another tab writes it. Anything else arriving is a root.
const AYAH_REF = /^(\d+):(\d+)$/

const SURAH_MIN = 1
const SURAH_MAX = 114

export default function QuranLookup({ accent, incoming, arrival, onGo, onVisit }) {
  // What arrived from another tab, if it was an ayah address.
  const arrived = AYAH_REF.exec(incoming ?? '')

  const [mode, setMode] = useState('ref')
  const [surah, setSurah] = useState(arrived?.[1] ?? '')
  const [ayah, setAyah] = useState(arrived?.[2] ?? '')
  const [query, setQuery] = useState('')
  // What is typed in the surah-and-ayah box, kept apart from the two number
  // fields so half a name never overwrites a number already chosen.
  const [typedRef, setTypedRef] = useState('')
  // The ayahs a recitation might have been. Kept apart from the typed search's
  // results because they are a different claim: a search found these words, a
  // recitation was guessed at twice over, once by the listening and once by the
  // matching. Only one of the two lists is ever on screen.
  const [heard, setHeard] = useState(null)
  // Which surah is open for reading, or null. Separate from the ayah lookup so
  // closing the reader leaves the ayah you were on untouched.
  const [reading, setReading] = useState(null)

  const { history: recent, push: remember } = useHistory('quran-history')

  // An ayah that came back is a place reached, written the way every other tab
  // writes one, so the trail and the back arrow can carry it. See lib/journey.js.
  const ayahLookup = useMutation({
    mutationFn: ({ s, a }) => getQuranAyah(s, a),
    onSuccess: (_, { s, a }) => { remember({ surah: s, ayah: a }); onVisit?.(`${s}:${a}`) },
  })
  const search = useMutation({ mutationFn: searchQuran })
  const rootLookup = useMutation({ mutationFn: getQuranRoot })

  // Two different things can arrive and they are told apart by their shape,
  // because they were not before: Daleel hands over an ayah address like "1:3",
  // the Dictionary hands over a root, and every arrival was looked up as a
  // root. An ayah address is not a root, so "Open the ayah" answered "the root
  // does not occur in the Qur'an" for an ayah sitting in the Qur'an.
  const { mutate: lookupRoot } = rootLookup
  const { mutate: lookupAyahRef } = ayahLookup

  // The fields follow an arrival during the render. App no longer remounts this
  // panel for one, that remount faded the whole page back in and read as a
  // flash (see lib/useArrival), and what the last arrival left open is not
  // about this one: a surah left open for reading would sit on top of the ayah
  // just asked for, and a list of heard ayahs would sit under it.
  // `arrived` above is the ayah address this word parses into, if any; this is
  // whether it has just come in.
  const { arrived: justCame } = useArrival(arrival)
  if (justCame && incoming) {
    setReading(null)
    setHeard(null)
    if (arrived) {
      setMode('ref')
      setSurah(arrived[1])
      setAyah(arrived[2])
    }
  }

  useEffect(() => {
    if (!incoming) return
    if (arrived) lookupAyahRef({ s: Number(arrived[1]), a: Number(arrived[2]) })
    else lookupRoot(incoming)
    // `arrived` is derived from `incoming` on every render, so the address
    // itself is the dependency worth naming.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [arrival, incoming, lookupRoot, lookupAyahRef])

  const lookupAyah = () => {
    if (surah && ayah) ayahLookup.mutate({ s: Number(surah), a: Number(ayah) })
  }
  const runSearch = () => {
    const trimmed = query.trim()
    setHeard(null)
    if (trimmed) search.mutate(trimmed)
  }

  // What came back from the microphone: the words go in the box so they can be
  // corrected and searched normally, and the ayahs are offered to tap. Shaped
  // like a search result so the same list draws them, rather than a second list
  // that would have to be kept looking like the first one.
  const onHeard = ({ text, ayahs }) => {
    setQuery(text || '')
    search.reset()
    setHeard(
      (ayahs || []).map((hit) => ({
        surah: hit.surah,
        ayah: hit.ayah,
        arabic_text: hit.arabic,
        source: { key: 'recitation', label: 'Heard on this machine', confidence: 'guessed' },
      })),
    )
  }
  const readSurah = (n) => { setMode('ref'); setReading(n) }

  const openResult = (r) => {
    setSurah(String(r.surah))
    setAyah(String(r.ayah))
    setMode('ref')
    ayahLookup.mutate({ s: r.surah, a: r.ayah, d: false })
  }

  const busy = ayahLookup.isPending || search.isPending

  return (
    <div className="space-y-6">
      <SectionHeader title="Quran" arabic="القرآن" />

      <div
        className="flex p-1 rounded-[var(--radius-md)] bg-[var(--surface)] border border-[var(--border)]"
        role="group"
        aria-label="Lookup mode"
      >
        {MODES.map((m) => (
          <button
            key={m.id}
            type="button"
            onClick={() => setMode(m.id)}
            aria-pressed={mode === m.id}
            style={mode === m.id ? { background: accent, color: 'var(--bg)' } : undefined}
            className={`flex-1 py-2 rounded-[var(--radius-sm)] text-sm font-medium transition-colors ${
              mode === m.id ? '' : 'text-[var(--text-faint)] hover:text-[var(--text)]'
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {mode === 'ref' && recent.length > 0 && (
        <RecentRow
          items={recent.map((h) => `${h.surah}:${h.ayah}`)}
          accent={accent}
          onPick={(item) => {
            const [s, a] = item.split(':')
            openResult({ surah: Number(s), ayah: Number(a) })
          }}
          mono
        />
      )}

      {mode === 'ref' && (
        <SurahRefBox
          value={typedRef} onChange={setTypedRef} busy={busy} accent={accent}
          onOpen={(m, a) => (a === null ? readSurah(m.n) : openResult({ surah: m.n, ayah: a }))}
        />
      )}

      {mode === 'ref' ? (
        <ReferenceForm
          surah={surah} ayah={ayah}
          onSurah={setSurah} onAyah={setAyah}
          onSubmit={lookupAyah} busy={busy} accent={accent}
        />
      ) : (
        <SearchForm
          query={query} onChange={setQuery} onSubmit={runSearch} onHeard={onHeard}
          busy={busy} accent={accent}
        />
      )}

      {(ayahLookup.isError || search.isError) && (
        <ErrorAlert title="Lookup failed">
          {/* Not "could not reach Quran.com" any more: a search that cannot
              reach it falls back to the local index and never errors here, so
              reaching this line means the app's own backend did not answer. */}
          {smartError(ayahLookup.error || search.error, 'Could not reach the backend. Check that it is running.')}
          <RetryButton onClick={ayahLookup.isError ? lookupAyah : runSearch} />
        </ErrorAlert>
      )}

      {rootLookup.isError && (
        <ErrorAlert title="Root not found">
          {smartError(rootLookup.error, 'That root does not occur in the Qur’an.')}
        </ErrorAlert>
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

      {reading && (
        <SurahReader
          surah={reading}
          accent={accent}
          onChangeSurah={setReading}
          onClose={() => setReading(null)}
          onOpenAyah={openResult}
        />
      )}

      {/* Search matches sit directly under the search form, and only while
          that form is showing: drawn after the opened ayah they were nine
          screens down the page, and pressing Search looked like it had done
          nothing. The opened ayah stays put underneath in either mode, since
          switching the form is not closing the ayah being read. */}
      {mode === 'search' && (
        heard ? (
          <SearchResults results={heard} onSelect={(r) => { setHeard(null); openResult(r) }} accent={accent} />
        ) : search.data ? (
          <div aria-busy={search.isPending} className={`transition-opacity ${search.isPending ? 'opacity-60' : ''}`}>
            <SearchResults results={search.data} onSelect={openResult} accent={accent} />
          </div>
        ) : (
          search.isPending && <AnalyzerSkeleton />
        )
      )}
      {/* A lookup in flight keeps the previous answer on screen, dimmed, rather
          than blanking it: swapping to the skeleton for every keystroke-driven
          retry read as the tool losing what it just found. Only a first-ever
          lookup with nothing to hold onto shows the skeleton. */}
      {ayahLookup.data ? (
        <div aria-busy={ayahLookup.isPending} className={`transition-opacity ${ayahLookup.isPending ? 'opacity-60' : ''}`}>
          <AyahStudy data={ayahLookup.data} onGo={onGo} onReadSurah={readSurah} accent={accent} />
        </div>
      ) : (
        ayahLookup.isPending && <AnalyzerSkeleton />
      )}
    </div>
  )
}

function ReferenceForm({ surah, ayah, onSurah, onAyah, onSubmit, busy, accent }) {
  const surahNumber = Number(surah)
  const surahInvalid = Boolean(surah) && (
    !Number.isInteger(surahNumber) || surahNumber < SURAH_MIN || surahNumber > SURAH_MAX
  )

  return (
    <div className="space-y-3">
      <div className="flex gap-3">
        <NumberField
          id="surah-input" label="Surah" value={surah} onChange={onSurah}
          min={SURAH_MIN} max={SURAH_MAX} placeholder={`${SURAH_MIN}–${SURAH_MAX}`}
          invalid={surahInvalid} hint={surahInvalid ? `Must be ${SURAH_MIN}–${SURAH_MAX}` : null}
          accent={accent} onEnter={onSubmit}
        />
        <NumberField
          id="ayah-input" label="Ayah" value={ayah} onChange={onAyah}
          min={1} placeholder="e.g. 255" accent={accent} onEnter={onSubmit}
        />
      </div>

      {!surah && !ayah && (
        <p className="text-[var(--text-faint)] type-small">
          Try 2:255 (Ayat al-Kursi) or 1:1 (the opening of al-Fatiha).
        </p>
      )}

      <PrimaryButton
        accent={accent}
        disabled={busy || !surah || !ayah || surahInvalid}
        loading={busy}
        onClick={onSubmit}
      >
        {busy ? 'Loading…' : 'Look up ayah'}
      </PrimaryButton>
    </div>
  )
}

function SearchForm({ query, onChange, onSubmit, onHeard, busy, accent }) {
  return (
    <div className="space-y-3">
      {/* The same field as the Dictionary and Daleel. Arabic only here, because
          the mushaf is only in Arabic and this box searches its words, so the
          box stays turned round rather than waiting to be told. */}
      <SearchBox
        id="quran-search"
        label="Arabic word or phrase"
        hint="Enter to search, or recite it"
        placeholder="ابحث عن كلمة..."
        value={query}
        onChange={onChange}
        onSubmit={onSubmit}
        busy={busy}
        accent={accent}
        arabic
      >
        <MicButton onHeard={onHeard} match accent={accent} title="Recite an ayah" />
      </SearchBox>
      {/* Only once they are actually on screen: before that the advice has
          nothing to act on, and an empty box is the one moment it cannot apply. */}
      {hasDiacritics(query) && (
        <p className="text-[var(--text-faint)] type-small">
          Diacritics are optional; leaving them off matches more.
        </p>
      )}
      <PrimaryButton accent={accent} disabled={busy || !query.trim()} loading={busy} onClick={onSubmit}>
        {busy ? 'Searching…' : 'Search the Quran'}
      </PrimaryButton>
    </div>
  )
}

function NumberField({ id, label, value, onChange, min, max, placeholder, invalid = false, hint, accent, onEnter }) {
  return (
    <div className="flex-1">
      <label htmlFor={id} className="text-[var(--text-faint)] text-xs uppercase tracking-wide block mb-1">
        {label}
      </label>
      <input
        id={id}
        type="number"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && onEnter?.()}
        placeholder={placeholder}
        aria-invalid={invalid || undefined}
        style={{
          '--c': invalid ? 'var(--danger)' : accent,
          borderColor: invalid ? 'var(--danger)' : 'var(--border)',
        }}
        className="w-full rounded-[var(--radius-md)] p-3 bg-[var(--surface)] text-[var(--text)]
          border focus:border-[var(--c)] focus:outline-none transition-colors"
      />
      {hint && <p className="text-xs mt-1" style={{ color: 'var(--danger)' }}>{hint}</p>}
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
        <p className="text-[var(--text-dim)] text-sm">{results.length} matches, pick one to open it</p>
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
          <div className="text-[var(--text-faint)] text-xs mb-1 font-mono">{r.surah}:{r.ayah}</div>
          <ArabicText as="div" className="text-right text-[var(--text)]">{r.arabic_text}</ArabicText>
        </button>
      ))}
    </div>
  )
}

function RootView({ data, accent, onGo, onOpenAyah, onClose }) {
  const shown = data.occurrences.length

  return (
    <div className="space-y-4 rise-in">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-baseline gap-3 flex-wrap">
          <ArabicText size="lg" className="text-[var(--text)]">{data.root}</ArabicText>
          <span className="text-sm text-[var(--text-dim)]">
            appears <strong className="text-[var(--text)] tabular-nums">{data.total}</strong> times in the Qur&rsquo;an
          </span>
        </div>
        <div className="flex items-center gap-2">
          <SourceBadge source={data.source} />
          <button
            type="button"
            onClick={onClose}
            className="text-xs text-[var(--text-faint)] hover:text-[var(--text)] underline underline-offset-2"
          >
            Close
          </button>
        </div>
      </div>

      {data.forms.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs text-[var(--text-faint)]">Words built from it, commonest first</p>
          <div className="flex flex-wrap gap-1.5">
            {data.forms.map((f) => (
              <span
                key={`${f.lemma}-${f.pos}`}
                className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full
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
        <p className="text-xs text-[var(--text-faint)]">
          {shown < data.total
            ? `First ${shown} of ${data.total} places, pick one to open it`
            : `All ${shown} places, pick one to open it`}
        </p>
        <div className="grid sm:grid-cols-2 gap-1.5">
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
}
