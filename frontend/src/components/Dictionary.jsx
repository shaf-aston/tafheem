/** Arabic to English, and back the other way. */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { rootBabsQuery, searchDictionary, translateSentence } from '../api'
import config from '../dictionary.json'
import { isArabic } from '../lib/arabicText'
import { entrySpan } from '../lib/entrySpan'
import { plainPronunciation } from '../lib/pronounce'
import { pickRoots } from '../lib/rootKey'
import { useSetting } from '../lib/settings'
import { useHealth } from '../lib/useHealth'
import { useSearch } from '../lib/useSearch'

import LexiconShelf from './LexiconShelf'
import RootMeaningCard from './RootMeaningCard'
import SentenceMeaning from './SentenceMeaning'
import ArabicText from './ui/ArabicText'
import Chip from './ui/Chip'
import ChipRow from './ui/ChipRow'
import EmptyState from './ui/EmptyState'
import ErrorAlert from './ui/ErrorAlert'
import ExampleChips from './ui/ExampleChips'
import MicButton from './ui/MicButton'
import PlaceLinks from './ui/PlaceLinks'
import Pronunciation from './ui/Pronunciation'
import RecentRow from './ui/RecentRow'
import RootActions from './ui/RootActions'
import SearchBox from './ui/SearchBox'
import SectionHeader from './ui/SectionHeader'
import SenseBands from './ui/SenseBands'
import VerbFormTag from './ui/VerbFormTag'
import { AnalyzerSkeleton } from './ui/Skeleton'
import { CorrectedNote } from './ui/StatusNote'
import SourceBadge from './ui/SourceBadge'
import WordGrid from './ui/WordGrid'
import Code from './ui/Code'

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

/**
 * Arabic of two words or more is a phrase or a sentence, and wants translating
 * rather than looking up. A word is two letters or more: ك ت ب is one root
 * spelled out, not three words.
 */
const isSentence = (text) => languageOf(text) === 'ar' && text.split(/\s+/).filter((w) => w.length > 1).length > 1

export default function Dictionary({ accent, incoming, arrival, onGo, onVisit }) {
  const { dictionaryLoaded } = useHealth()
  const missing = dictionaryLoaded === false

  // How many Recent keeps is session.json's recent-kept; unlimited buried the
  // search box under forty words on a phone. The place reached is the word the
  // server searched, not the keystrokes: "ك ت ب" comes back as كتب, and it is
  // كتب that belongs in Recent and in the trail. An arriving word is read the
  // same way as one typed: the command bar can hand over either language.
  const { query, setQuery, history, mutation, submit: lookUp, clear, shown } = useSearch({
    historyKey: 'dict-history',
    ask: ({ q }) => (isSentence(q) ? translateSentence(q) : searchDictionary(q, languageOf(q))),
    place: (data) => data.query,
    onVisit,
    incoming,
    arrival,
  })

  // No dictionary installed: the alert above already says so; a request would
  // only come back as a misleading "No entries". Following a synonym is a new
  // search too, put in the box so the reader can see where they have got to.
  const submit = (given) => { if (!missing) lookUp(given) }

  return (
    <div className="panel">
      <SectionHeader
        title="Dictionary"
        arabic="قاموس"
        subtitle="Search an Arabic word, a root or an English meaning, or translate a whole Arabic sentence."
      />

      {/* Say the dictionary is not installed rather than letting every search
          come back "No entries", which reads like the word was not found. */}
      {missing && (
        <ErrorAlert title="Dictionary not installed">
          No dictionary data on this machine, so every search would come back empty.
          Build it with{' '}
          <Code>
            python backend/scripts/build_dictionary.py
          </Code>
        </ErrorAlert>
      )}

      {/* Every recent word, whichever language it was in: they were split into
          two lists by the toggle that used to sit above, and half of them were
          hidden at any one time. Each chip is set in its own script. */}
      <RecentRow
        items={history.map((h) => h.q)}
        accent={accent}
        onPick={submit}
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
          onClear={clear}
          busy={mutation.isPending}
          disabled={missing}
          accent={accent}
        >
          {/* A word, not an ayah: the dictionary looks up whatever was said,
              so it asks only for the words and never for a list of ayahs. */}
          <MicButton
            onHeard={({ text }) => { setQuery(text); mutation.reset() }}
            accent={accent}
            title="Say the word"
          />
        </SearchBox>

        <PlaceLinks query={query} onGo={onGo} accent={accent} />

        {/* True whichever language is typed, so it no longer waits on a toggle
            to be set the right way before it can be read. */}
        {!query && !shown && (
          <>
            <p className="text-[var(--text-faint)] type-small">
              Roots work best; كتب finds the whole family of words built on it.
            </p>
            {/* First visit has nothing to click; these give it something. */}
            <ExampleChips
              examples={config.examples}
              onPick={submit}
              accent={accent}
            />
          </>
        )}

      </div>

      {mutation.isError && (
        <ErrorAlert title="Search failed" error={mutation.error} fallback="The dictionary file may not be installed yet." onRetry={() => submit()} />
      )}

      {mutation.isPending && !shown && <AnalyzerSkeleton />}

      <CorrectedNote corrected={shown?.corrected} />

      {shown?.words && <SentenceMeaning data={shown} accent={accent} onGo={onGo} onLookup={submit} />}
      {shown?.results && <Results data={shown} accent={accent} onGo={onGo} onLookup={submit} />}

      {/* Under the word results, not above them: the meaning searched for is the
          answer, and the root's origin sense is the wider context behind it. On a
          phone the card was pushing the entries a whole screen down. Arabic only,
          Maqayees is a root book, so an English search has no root to ask about. */}
      {/* Keyed by the search: a new search is a new question, so the choice of
          root starts over on the one it found. */}
      {shown?.lang === 'ar' && <ClassicalRoot key={shown.query} found={shown} accent={accent} />}
    </div>
  )
}

/**
 * The two classical cards, and which root they ask about.
 *
 * One root for both, because they must ask about the same one: مدرسة finds
 * nothing in any of the books and درس finds all of it, and a choice that moved
 * only the card it sits in left the other saying the root does not exist. The
 * chips sit above both, not inside one, for the same reason.
 */
function ClassicalRoot({ found, accent }) {
  const { primary, alternates } = pickRoots(found.query, found.results)
  const [root, setRoot] = useState(primary)
  const hasAlternates = alternates.length > 0
  return (
    <>
      {hasAlternates && (
        <ChipRow label="Which root to look up" role="group" aria-label="Which root to look up">
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
        </ChipRow>
      )}
      <RootMeaningCard root={root} hasAlternates={hasAlternates} accent={accent} />
      {/* Under the short answer: the books it was drawn from, for a reader who
          wants more than a sentence. */}
      <LexiconShelf root={root} hasAlternates={hasAlternates} accent={accent} />
    </>
  )
}

function Results({ data, accent, onGo, onLookup }) {
  // The badge at the top right opens the references behind the bab names.
  const [refs, setRefs] = useState(false)
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
        <button
          type="button"
          onClick={() => setRefs((on) => !on)}
          aria-expanded={refs}
          aria-label="Show where each bab is recorded"
        >
          <SourceBadge source={data.source} />
        </button>
      </div>

      {/* Two questions, two shapes. An Arabic word asks what it means, and the
          answer is one entry read in full. An English word asks which words
          carry that meaning, and the answer is the candidates side by side; the
          same full entries were a page and a half of scrolling to compare two
          of them. See ui/WordGrid.jsx. */}
      {data.lang === 'en' ? (
        <WordGrid results={data.results} query={data.query} accent={accent} onGo={onGo} />
      ) : (
        <Forms results={data.results} accent={accent} onGo={onGo} onLookup={onLookup} refs={refs} />
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
function Forms({ results, accent, onGo, onLookup, refs }) {
  const [lead, ...others] = results
  return (
    <>
      <Entry entry={lead} accent={accent} i={0} onGo={onGo} onLookup={onLookup} refs={refs} />
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

/** The root's Form I باب from the classical books; nothing at all when none records one. */
function RootBabs({ root, refs }) {
  const { data } = useQuery(rootBabsQuery(root))
  return data?.readings.length ? <VerbFormTag readings={data.readings} plain showSources={refs} /> : null
}

/**
 * One dictionary entry. Full for the word searched; compact for the words
 * beside it, where the root is left off when it is the same one printed
 * above, and the card spans more columns when it holds more than a glance.
 * One type scale throughout (styles/text.css tokens): a card holding eight senses
 * reads at the same size as one holding a single line, only its footprint
 * differs.
 */
function Entry({ entry, accent, i, onGo, onLookup, refs = false, compact = false, sameRoot = false }) {
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
      {/* Two rows: word beside its sound, root beside its bab (from the books, never typed in). */}
      <div className="grid grid-cols-[auto_auto] justify-between items-baseline gap-x-3 gap-y-0.5" dir="rtl">
        <ArabicText as="div" style={{ color: accent }}>{entry.arabic}</ArabicText>
        <Pronunciation size="body">{entry.transliteration}</Pronunciation>
        {entry.root && !sameRoot && (
          <ArabicText as="div" className="text-[var(--text-faint)]">جذر: {entry.root}</ArabicText>
        )}
        {!compact && entry.root && <div dir="ltr"><RootBabs root={entry.root} refs={refs} /></div>}
      </div>

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

      {entry.root && (
        // showRoot=false: the root already prints above under "جذر:", so the
        // bare repeat inside RootActions is dropped.
        <RootActions root={entry.root} onGo={onGo} exclude="dict" showRoot={false} />
      )}
    </div>
  )
}
