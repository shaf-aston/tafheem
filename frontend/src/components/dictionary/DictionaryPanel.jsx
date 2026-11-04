/** Arabic to English, and back the other way. */
import { useState } from 'react'

import { searchDictionary, translateSentence } from '../../api'
import config from '../../config/dictionary.json'
import { isArabic } from '../../lib/text/arabicText'
import { classicalBooks, MAQAYEES, useLexicons } from '../../lib/dictionary/classicalBooks'
import { pickRoots } from '../../lib/dictionary/rootKey'
import { scrollToEl } from '../../lib/motion/scrollToEl'
import { useHealth } from '../../lib/api/useHealth'
import { useRemembered } from '../../lib/store/useRemembered'
import { useSearch } from '../../lib/hooks/useSearch'

import LexiconShelf from './LexiconShelf'
import RootMeaningCard from './RootMeaningCard'
import SentenceMeaning from '../ui/text/SentenceMeaning'
import Chip from '../ui/inputs/Chip'
import ChipRow from '../ui/inputs/ChipRow'
import ErrorAlert from '../ui/feedback/ErrorAlert'
import ExampleChips from '../ui/inputs/ExampleChips'
import MicButton from '../ui/buttons/MicButton'
import PlaceLinks from '../ui/text/PlaceLinks'
import RecentRow from '../ui/inputs/RecentRow'
import SearchBox from '../ui/inputs/SearchBox'
import SectionHeader from '../ui/display/SectionHeader'
import { AnalyzerSkeleton } from '../ui/feedback/Skeleton'
import { CorrectedNote } from '../ui/feedback/StatusNote'
import WordEntry, { ReadAsNote } from './WordEntry'
import Code from '../ui/text/Code'

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
 * Two words or more, in either language, is a phrase or a sentence, and wants
 * translating rather than looking up. A word is two letters or more: ك ت ب is
 * one root spelled out, not three words.
 */
const isSentence = (text) => text.split(/\s+/).filter((w) => w.length > 1).length > 1

export default function DictionaryPanel({ accent, incoming, arrival, onGo, onVisit }) {
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
      <SectionHeader tab="dict" answered={Boolean(shown)}
        subtitle="Search an Arabic word, a root or an English meaning, or translate a whole Arabic sentence."
      />

      {/* Say the dictionary is not installed rather than letting every search
          come back "No entries", which reads like the word was not found. */}
      {missing && (
        <ErrorAlert title="Dictionary not installed">
          No dictionary data on this machine, so every search would come back empty.
          Build it with{' '}
          <Code>
            python backend/scripts/dictionary/build_dictionary.py
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
          verb="search"
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
      <ReadAsNote readAs={shown?.read_as} />

      {shown?.words && <SentenceMeaning data={shown} accent={accent} onGo={onGo} onLookup={submit} />}
      {/* The classical books sit under every word card, three or four screens
          down on a phone; this is the way to them without the scroll. */}
      {shown?.results && (
        <WordEntry data={shown} accent={accent} onGo={onGo} onLookup={submit}
          aside={shown.lang === 'ar' && (
            <button
              type="button"
              onClick={() => scrollToEl(document.getElementById(CLASSICAL), 'top')}
              style={{ '--c': accent }}
              className="tap type-small text-[var(--text-faint)] hover:text-[var(--c)] transition-colors me-auto"
            >
              Classical dictionaries ↓
            </button>
          )} />
      )}

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
/** Where the jump to the classical books lands. */
const CLASSICAL = 'dict-classical'

function ClassicalRoot({ found, accent }) {
  // The root the search worked out, when it did (مُنْتَصِرًا is نصر); the word as typed otherwise.
  const { primary, alternates } = pickRoots(found.root || found.query, found.results)
  const [root, setRoot] = useState(primary)
  const hasAlternates = alternates.length > 0
  // One book at a time, from one switch. Four books on a common root ran to
  // ten screens on a phone, Lane fourth and a reader scrolling past three
  // Arabic walls to reach the one in English. The choice is remembered: a
  // reader who reads Lane keeps Lane from root to root.
  const { data: shelf } = useLexicons(root)
  const books = classicalBooks(shelf?.entries)
  const [book, setBook] = useRemembered('dict.book', books.map((one) => one.id))
  // One frame round every book, not a frame per book inside a frame per shelf:
  // three borders deep, the page read as boxes before it read as dictionaries.
  // The books are ruled off from each other instead.
  return (
    <section
      id={CLASSICAL}
      aria-label="Classical dictionaries"
      className="rounded-[var(--radius-md)] border border-[var(--border)] overflow-hidden scroll-mt-24"
    >
      <header className="px-4 py-2.5 bg-[var(--surface)] flex items-center gap-x-3 gap-y-2 flex-wrap">
        <h3 className="type-body font-medium text-[var(--text)]">Classical dictionaries</h3>
        {hasAlternates && (
          <ChipRow label="Root" role="group" aria-label="Which root to look up">
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
      </header>
      {books.length > 1 && (
        // Chips on one sliding line, the root row's own shape: as a segmented
        // control four names wrapped on a phone and left Lane alone on a second row.
        <ChipRow scroll role="group" aria-label="Which book" className="px-4 pt-3">
          {books.map((one) => (
            <Chip key={one.id} accent={accent} selected={book === one.id} onClick={() => setBook(one.id)}>
              {one.label}
            </Chip>
          ))}
        </ChipRow>
      )}
      {/* Hidden, not unmounted: an entry opened, or put into English, is as it
          was left when the reader comes back to its book. */}
      <div hidden={book !== MAQAYEES}>
        <RootMeaningCard root={root} hasAlternates={hasAlternates} accent={accent} />
      </div>
      <LexiconShelf root={root} shown={book} hasAlternates={hasAlternates} accent={accent} />
    </section>
  )
}
