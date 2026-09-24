/** Arabic to English, and back the other way. */
import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { searchDictionary } from '../api'
import { smartError } from '../lib/apiError'
import { isArabic } from '../lib/arabicText'
import { entrySpan } from '../lib/entrySpan'
import { plainPronunciation } from '../lib/pronounce'
import { pickRoots } from '../lib/rootKey'
import { useSetting } from '../lib/settings'
import { useHealth } from '../lib/useHealth'
import { useArrival, useHeld } from '../lib/useArrival'
import { useHistory } from '../lib/useHistory'

import LexiconShelf from './LexiconShelf'
import RootMeaningCard from './RootMeaningCard'
import ArabicText from './ui/ArabicText'
import Chip from './ui/Chip'
import EmptyState from './ui/EmptyState'
import ErrorAlert from './ui/ErrorAlert'
import ExampleChips from './ui/ExampleChips'
import MicButton from './ui/MicButton'
import Pronunciation from './ui/Pronunciation'
import RecentRow from './ui/RecentRow'
import RetryButton from './ui/RetryButton'
import RootActions from './ui/RootActions'
import SearchBox from './ui/SearchBox'
import SectionHeader from './ui/SectionHeader'
import SenseBands from './ui/SenseBands'
import { AnalyzerSkeleton } from './ui/Skeleton'
import SourceBadge from './ui/SourceBadge'
import WordGrid from './ui/WordGrid'

// Tailwind needs the literal class names present in source to keep them in the
// build; a computed string like `sm:col-span-${n}` would be purged.
const SPAN_CLASS = { 2: 'sm:col-span-2', 3: 'sm:col-span-2 lg:col-span-3' }

/**
 * Which way round a search is, worked out from the writing itself.
 *
 * There used to be a toggle above the box saying Arabic to English or the
 * other way, and it was answering a question the typing had already answered:
 * كتب can only be the one, "book" can only be the other. It could also be set
 * wrong, and a wrong setting looked exactly like a word the dictionary did not
 * have. Neither, digits or punctuation on their own, is read as Arabic, since
 * this is an Arabic dictionary being asked the question.
 */
const languageOf = (text) => (/[a-z]/i.test(text) && !isArabic(text) ? 'en' : 'ar')

export default function Dictionary({ accent, incoming, arrival, onGo, onVisit }) {
  const [query, setQuery] = useState(incoming ?? '')

  // 16, judged in the running app: one row on desktop, three short rows on a
  // phone. Unlimited was tried and forty words buried the search box there.
  const { history, push: remember } = useHistory('dict-history')
  const { dictionaryLoaded } = useHealth()
  const missing = dictionaryLoaded === false

  // A word that came back is a place reached: it goes in the Recent row and
  // into the trail, which is what puts it in the address bar and makes the
  // browser's back arrow land on the previous word. See lib/journey.js.
  const mutation = useMutation({
    mutationFn: ({ q, l }) => searchDictionary(q, l),
    // The word the server searched, not the keystrokes: "ك ت ب" comes back as
    // كتب, and it is كتب that belongs in Recent and in the trail.
    onSuccess: (data) => { remember({ q: data.query }); onVisit?.(data.query) },
  })

  const submit = (overrideQuery) => {
    // No dictionary installed: the alert above already says so; a request would
    // only come back as a misleading "No entries".
    if (missing) return
    const trimmed = (overrideQuery ?? query).trim()
    if (!trimmed) return
    mutation.mutate({ q: trimmed, l: languageOf(trimmed) })
  }

  // Following a synonym is a new search: the box shows the word being looked
  // up, so the reader can see where they have got to and can edit it.
  const lookUpWord = (word) => {
    setQuery(word)
    submit(word)
  }

  // A word arriving: handed over from another tab, or the back arrow returning
  // to one. App no longer remounts the panel for it, that remount faded the
  // whole page back in and read as a flash (see lib/useArrival), so the box
  // follows the word here, during the render.
  const { arrived, returning } = useArrival(arrival, mutation.isPending)
  if (arrived && incoming) setQuery(incoming)

  // Through a return the entries already read stay up until the new ones land.
  // A search the reader typed still clears them for the skeleton below: that is
  // a new question, and this is not.
  const shown = useHeld(mutation.isPending ? undefined : mutation.data, returning)

  // And it is looked up, read the same way as one typed: the command bar can
  // hand over either language.
  const { mutate: lookUp } = mutation
  useEffect(() => {
    if (incoming) lookUp({ q: incoming, l: languageOf(incoming) })
  }, [arrival, incoming, lookUp])

  // Which root the two classical cards below are asking about. Held here, one
  // level above both, because they must ask about the same one: مدرسة finds
  // nothing in any of the books and درس finds all of it, and a choice that
  // moved only the card it sits in left the other saying the root does not
  // exist. The chips are drawn once, above both, for the same reason.
  const { primary, alternates } = pickRoots(shown?.query, shown?.results)
  const [root, setRoot] = useState(primary)
  // A new search is a new question: go back to asking about what was typed.
  useEffect(() => { setRoot(primary) }, [primary])

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Dictionary"
        arabic="قاموس"
        subtitle="Searchable by Arabic word, by root, or by English meaning."
      />

      {/* Say the dictionary is not installed rather than letting every search
          come back "No entries", which reads like the word was not found. */}
      {missing && (
        <ErrorAlert title="Dictionary not installed">
          No dictionary data on this machine, so every search would come back empty.
          Build it with{' '}
          <code className="px-1 rounded bg-[var(--surface-hi)] text-[var(--text)]">
            python backend/scripts/build_dictionary.py
          </code>
        </ErrorAlert>
      )}

      {/* Every recent word, whichever language it was in: they were split into
          two lists by the toggle that used to sit above, and half of them were
          hidden at any one time. Each chip is set in its own script. */}
      <RecentRow
        items={history.map((h) => h.q)}
        accent={accent}
        onPick={(q) => { setQuery(q); submit(q) }}
      />

      <div className="space-y-3">
        {/* The same field as Daleel and the Qur'an tab, down to the keycap and
            the microphone: three tabs that take a word should not take it three
            different ways. See ui/SearchBox. */}
        <SearchBox
          id="dict-input"
          label="Arabic or English"
          hint="Enter to search, or say it"
          placeholder="Search كتب or book"
          value={query}
          onChange={setQuery}
          onSubmit={submit}
          onClear={() => { setQuery(''); mutation.reset() }}
          busy={mutation.isPending}
          disabled={missing}
          accent={accent}
        >
          {/* A word, not an ayah: the dictionary looks up whatever was said,
              so it asks only for the words and never for a list of ayahs. */}
          <MicButton
            onHeard={({ text }) => { setQuery(text || ''); mutation.reset() }}
            accent={accent}
            title="Say the word"
          />
        </SearchBox>

        {/* True whichever language is typed, so it no longer waits on a toggle
            to be set the right way before it can be read. */}
        {!query && !shown && (
          <>
            <p className="text-[var(--text-faint)] type-small">
              Roots work best; كتب finds the whole family of words built on it.
            </p>
            {/* First visit has nothing to click; these give it something. */}
            <ExampleChips
              examples={[
                { arabic: 'كتب', meaning: 'to write' },
                { arabic: 'رحم', meaning: 'mercy' },
                { arabic: 'علم', meaning: 'to know' },
              ]}
              onPick={lookUpWord}
              accent={accent}
            />
          </>
        )}

      </div>

      {mutation.isError && (
        <ErrorAlert title="Search failed">
          {smartError(mutation.error, 'The dictionary file may not be installed yet.')}
          <RetryButton onClick={() => submit()} />
        </ErrorAlert>
      )}

      {mutation.isPending && !shown && <AnalyzerSkeleton />}

      {shown && (
        <Results data={shown} accent={accent} onGo={onGo} onLookup={lookUpWord} />
      )}

      {/* Under the word results, not above them: the meaning searched for is the
          answer, and the root's origin sense is the wider context behind it. On a
          phone the card was pushing the entries a whole screen down. Arabic only,
          Maqayees is a root book, so an English search has no root to ask about. */}
      {shown?.lang === 'ar' && (
        <>
          {/* Above both cards, not inside one, because it moves both. A word
              like مدرسة is not itself a root; the root it is built on is
              offered, and the books answer on whichever is chosen. */}
          {alternates.length > 0 && (
            <div
              className="flex flex-wrap gap-1.5 items-center"
              role="group"
              aria-label="Which root to look up"
            >
              <span className="text-[var(--text-faint)] type-small shrink-0">
                Which root to look up
              </span>
              {[primary, ...alternates].map((one) => (
                <Chip
                  key={one}
                  arabic
                  accent={accent}
                  selected={root === one}
                  onClick={() => setRoot(one)}
                >
                  {one}
                </Chip>
              ))}
            </div>
          )}
          <RootMeaningCard root={root} hasAlternates={alternates.length > 0} accent={accent} />
          {/* Under the short answer, and shut: the books it was drawn from, for
              a reader who wants more than a sentence. */}
          <LexiconShelf root={root} hasAlternates={alternates.length > 0} />
        </>
      )}
    </div>
  )
}

function Results({ data, accent, onGo, onLookup }) {
  if (data.results.length === 0) {
    return (
      <EmptyState>No entries. Try the bare root, without prefixes or endings.</EmptyState>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        {/* One is the usual answer for a whole Arabic word, the dictionary is
            indexed by headword, but a part-word, a spaced root, or an English
            search all come back with several. */}
        <p className="text-[var(--text-dim)] type-body">
          {data.results.length === 1 ? '1 entry' : `${data.results.length} entries`}
        </p>
        <SourceBadge source={data.source} />
      </div>

      {/* Two questions, two shapes. An Arabic word asks what it means, and the
          answer is one entry read in full. An English word asks which words
          carry that meaning, and the answer is the candidates side by side; the
          same full entries were a page and a half of scrolling to compare two
          of them. See ui/WordGrid.jsx. */}
      {data.lang === 'en' ? (
        <WordGrid results={data.results} query={data.query} accent={accent} onGo={onGo} />
      ) : (
        <Forms results={data.results} accent={accent} onGo={onGo} onLookup={onLookup} />
      )}
    </div>
  )
}

/**
 * The searched word in full, and the other words on its root as small cards.
 *
 * The first result is the word asked about (the service puts the exact word
 * first), and it is read the way a dictionary entry is read. The rest are
 * there to be compared, أطلع against استطلع against اطلاع, so they sit side by
 * side in a grid, each card as wide as its senses need (lib/entrySpan.js) and
 * the gaps filled by whatever fits, so the eye moves across rather than down.
 * A drop-down would have hidden the very thing worth comparing.
 */
function Forms({ results, accent, onGo, onLookup }) {
  const [lead, ...others] = results
  return (
    <>
      <Entry entry={lead} accent={accent} i={0} onGo={onGo} onLookup={onLookup} />
      {others.length > 0 && (
        <>
          <p className="type-small text-[var(--text-faint)] pt-2">
            {others.length === 1 ? 'One more word on this root' : `${others.length} more words on this root`}
          </p>
          {/* Grid default (stretch) so every card in a row shares that row's
              height; a short card beside a tall one used to end early and read
              as a mismatched row rather than one grid. */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 grid-flow-dense">
            {others.map((entry, i) => (
              <Entry
                key={`${entry.arabic}-${entry.root || i}`}
                entry={entry}
                accent={accent}
                i={i + 1}
                onGo={onGo}
                onLookup={onLookup}
                compact
                sameRoot={entry.root === lead.root}
              />
            ))}
          </div>
        </>
      )}
    </>
  )
}

/**
 * One dictionary entry. Full for the word searched; compact for the words
 * beside it, where the root is left off when it is the same one printed
 * above, and the card spans more columns when it holds more than a glance.
 * One type scale throughout (index.css tokens): a card holding eight senses
 * reads at the same size as one holding a single line, only its footprint
 * differs.
 */
function Entry({ entry, accent, i, onGo, onLookup, compact = false, sameRoot = false }) {
  // Off by default for nobody, but one switch away for anyone who finds the
  // extra words distracting. Read here rather than passed down, so the switch
  // reaches the one place that draws them.
  const showSynonyms = useSetting('synonyms')
  const span = compact ? entrySpan(entry) : 1
  const wide = span >= 2

  return (
    <div
      style={{ '--i': i }}
      className={`rise-in rounded-[var(--radius-md)] bg-[var(--surface)] border border-[var(--border)]
        ${compact ? 'p-3 space-y-2' : 'p-4 space-y-3'} ${SPAN_CLASS[span] ?? ''}`}
    >
      <div className="flex items-start justify-between gap-3" dir="rtl" lang="ar">
        <div>
          <ArabicText as="div" style={{ color: accent }}>{entry.arabic}</ArabicText>
          {entry.root && !sameRoot && (
            <ArabicText as="div" className="text-[var(--text-faint)] mt-0.5">جذر: {entry.root}</ArabicText>
          )}
        </div>
        <Pronunciation size="body" className="mt-1">{entry.transliteration}</Pronunciation>
      </div>

      {entry.root && (
        // showRoot=false: the root already prints above under "جذر:", so the
        // bare repeat inside RootActions is dropped.
        <RootActions root={entry.root} onGo={onGo} exclude="dict" showRoot={false} />
      )}

      {/* A one-column card has no synonyms (that is what keeps it narrow), and
          the band's empty word column would squeeze its senses to a sliver. */}
      {entry.definitions?.length > 0 && (
        showSynonyms && !(compact && !wide) ? (
          <SenseBands
            definitions={entry.definitions}
            synonyms={entry.synonyms}
            accent={accent}
            onLookup={onLookup}
          />
        ) : (
          <ol className="list-decimal ps-6 min-w-0 space-y-1.5 type-body text-[var(--text)] marker:text-[var(--text-faint)]">
            {entry.definitions.map((d, n) => <li key={n}>{plainPronunciation(d)}</li>)}
          </ol>
        )
      )}

    </div>
  )
}
