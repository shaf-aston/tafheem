/** Arabic to English, and back the other way. */
import { useState } from 'react'

import { searchDictionary, translateSentence } from '../api'
import config from '../dictionary.json'
import { isArabic } from '../lib/arabicText'
import { pickRoots } from '../lib/rootKey'
import { useHealth } from '../lib/useHealth'
import { useSearch } from '../lib/useSearch'

import LexiconShelf from './dictionary/LexiconShelf'
import RootMeaningCard from './dictionary/RootMeaningCard'
import SentenceMeaning from './dictionary/SentenceMeaning'
import Chip from './ui/Chip'
import ChipRow from './ui/ChipRow'
import ErrorAlert from './ui/ErrorAlert'
import ExampleChips from './ui/ExampleChips'
import MicButton from './ui/MicButton'
import PlaceLinks from './ui/PlaceLinks'
import RecentRow from './ui/RecentRow'
import SearchBox from './ui/SearchBox'
import SectionHeader from './ui/SectionHeader'
import { AnalyzerSkeleton } from './ui/Skeleton'
import { CorrectedNote } from './ui/StatusNote'
import Results, { ReadAsNote } from './dictionary/WordEntry'
import Code from './ui/Code'

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
  // The root the search worked out, when it did (مُنْتَصِرًا is نصر); the word as typed otherwise.
  const { primary, alternates } = pickRoots(found.root || found.query, found.results)
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
