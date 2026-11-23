/** Arabic to English, and back the other way. */
import { useEffect, useRef, useState } from 'react'

import { searchDictionary, translateSentence } from '../../api'
import config from '../../config/dictionary.json'
import { isArabic } from '../../lib/text/arabicText'
import { classicalBooks, MAQAYEES, useLexicons } from '../../lib/dictionary/classicalBooks'
import { pickRoots } from '../../lib/dictionary/rootKey'
import { scrollToEl } from '../../lib/motion/scrollToEl'
import { useHealth } from '../../lib/api/useHealth'
import { useArrivalEffect } from '../../lib/nav/useArrival'
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
import PictureButton from '../ui/buttons/PictureButton'
import SmallButton from '../ui/buttons/SmallButton'
import { pictureIn } from '../../lib/dictionary/shrinkPicture'
import { onPageHanded, takePage } from '../../lib/dictionary/pageHandoff'
import PageReader from './PageReader'
import PlaceLinks from '../ui/text/PlaceLinks'
import RecentRow from '../ui/inputs/RecentRow'
import SearchBox from '../ui/inputs/SearchBox'
import QuestionForm from '../ui/inputs/QuestionForm'
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
  const { dictionaryLoaded, pageReader } = useHealth()
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
    // A word with no entries is not kept in Recent; a translated sentence has no entry list and always is.
    kept: (data) => !data.results || data.results.length > 0,
    onVisit,
    incoming,
    arrival,
  })

  // No dictionary installed: the alert above already says so; a request would
  // only come back as a misleading "No entries". Following a synonym is a new
  // search too, put in the box so the reader can see where they have got to.
  // A search, from the box, Recent or a page's word, is an answer to show: it closes the page (kept, see below).
  const submit = (given) => { if (!missing) { setPageOpen(false); lookUp(given) } }

  // A picture of a page: picked, pasted or dropped. The reader stays mounted
  // while a word from it is looked up, so "Back to the page" finds it as left.
  // Not until the server has said it can: while health loads, or when it failed, a picture would only 404.
  const canRead = Boolean(pageReader) && pageReader !== 'none'
  // The picture's address is made here, when it is picked, and let go when the next one or Close
  // replaces it: made inside the reader, React's second mount in development let it go too early.
  const [page, setPage] = useState(null)
  const [pageOpen, setPageOpen] = useState(false)
  const reader = useRef(null)
  const swapPage = (file) => {
    if (page) URL.revokeObjectURL(page.shown)
    setPage(file && { picture: file, shown: URL.createObjectURL(file), id: (page?.id ?? 0) + 1 })
    setPageOpen(Boolean(file))
  }
  const openPage = (file) => { if (file && canRead) swapPage(file) }
  const closePage = () => swapPage(null)
  // A new page, or the way back to one, brings the reader into sight: on a phone it opens below the fold.
  useEffect(() => { if (pageOpen) scrollToEl(reader.current, 'top') }, [pageOpen, page?.id])
  // A picture pasted while correcting the page's text is not a new page: it would throw the corrections away.
  const pasted = (event) => {
    const file = event.target.tagName !== 'TEXTAREA' && pictureIn(event.clipboardData)
    if (file && canRead) { event.preventDefault(); openPage(file) }
  }
  // Any file dropped here is ours, picture or not: left to the browser, a PDF would replace the whole app.
  // One that is no picture opens the reader all the same, which says what to send instead.
  const holdsFiles = (event) => canRead && [...(event.dataTransfer?.types ?? [])].includes('Files')
  const dropped = (event) => {
    if (!holdsFiles(event)) return
    event.preventDefault()
    openPage(pictureIn(event.dataTransfer) ?? event.dataTransfer.files[0])
  }
  // A picture handed from Home or the Ask sheet (lib/dictionary/pageHandoff): taken once this server can read,
  // at once if it was handed before the panel was here, or when it is handed while the panel already is.
  const opened = useRef(openPage)
  useEffect(() => { opened.current = openPage })
  useEffect(() => {
    if (!canRead) return
    const take = () => { const file = takePage(); if (file) opened.current(file) }
    take()
    return onPageHanded(take)
  }, [canRead])
  // Arriving from another tab with a word is a search: the page steps aside for it. Arriving with none
  // (the first mount counts) leaves it: a picture handed from Home has just opened it.
  useArrivalEffect(arrival, () => { if (arrival) setPageOpen(false) })
  // The picture's address is let go when the panel goes, as when a new picture replaces it.
  const lastPage = useRef(null)
  useEffect(() => { lastPage.current = page }, [page])
  useEffect(() => () => { if (lastPage.current) URL.revokeObjectURL(lastPage.current.shown) }, [])

  return (
    <div className="panel panel-search" onPaste={pasted} onDrop={dropped}
      onDragOver={(event) => { if (holdsFiles(event)) event.preventDefault() }}>
      <SectionHeader tab="dict" answered={Boolean(shown) || pageOpen}
        subtitle={`Search an Arabic word, a root or an English meaning, or translate a whole Arabic sentence${canRead ? '; or read a picture of a page.' : '.'}`}
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

      <QuestionForm>
        {/* The same field as Daleel and the Qur'an tab, down to the keycap and
            the microphone: three tabs that take a word should not take it three
            different ways. See ui/SearchBox. */}
        <SearchBox
          id="dict-input"
          label="Arabic or English"
          verb="search"
          placeholder="كتب or book"
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
          {canRead && <PictureButton onPicked={openPage} title="Read a picture of a page" />}
        </SearchBox>

        {/* Every recent word, whichever language it was in, each chip set in its
            own script. Under the box, not over it: what is typed leads, and on a
            wide screen the box sits level with the title with this beneath it. */}
        <RecentRow
          items={history.map((h) => h.q)}
          accent={accent}
          onPick={submit}
        />

        <PlaceLinks query={query} onGo={onGo} accent={accent} />

        {/* True whichever language is typed, so it no longer waits on a toggle
            to be set the right way before it can be read. */}
        {!query && !shown && !pageOpen && (
          <>
            {/* First visit has nothing to click; these give it something. */}
            <ExampleChips
              examples={config.examples}
              onPick={submit}
              accent={accent}
            />
          </>
        )}
      </QuestionForm>

      {page && (
        <div hidden={!pageOpen} ref={reader} className="scroll-mt-[calc(var(--app-header-h,0px)+1rem)]">
          <PageReader key={page.id} picture={page.picture} shown={page.shown} accent={accent} onClose={closePage} onLookup={missing ? null : submit} onGo={onGo} />
        </div>
      )}
      {page && !pageOpen && (
        <div><SmallButton onClick={() => setPageOpen(true)}>← Back to the page</SmallButton></div>
      )}

      {!pageOpen && mutation.isError && (
        <ErrorAlert title="Search failed" error={mutation.error} fallback="The dictionary file may not be installed yet." onRetry={() => submit()} />
      )}

      {!pageOpen && (
        <>
          {mutation.isPending && !shown && <AnalyzerSkeleton />}

          <AnswerFacts shown={shown} accent={accent} />

          {shown?.words && <SentenceMeaning data={shown} accent={accent} onGo={onGo} onLookup={submit} />}
          {shown?.results && <WordEntry data={shown} accent={accent} onGo={onGo} onLookup={submit} />}
        </>
      )}

      {/* Under the word results, not above them: the meaning searched for is the
          answer, and the root's origin sense is the wider context behind it. On a
          phone the card was pushing the entries a whole screen down. Arabic only,
          Maqayees is a root book, so an English search has no root to ask about. */}
      {/* Keyed by the search: a new search is a new question, so the choice of
          root starts over on the one it found. */}
      {!pageOpen && shown?.lang === 'ar' && <ClassicalRoot key={shown.query} found={shown} accent={accent} />}
    </div>
  )
}

/**
 * What there is to know about the answer before reading it, on one line: a
 * word the search swapped, what a form was read as, how many entries came
 * back, and the way down to the classical books. They were three rows between
 * the box and the answer; on a wide screen this line sits under the title,
 * beside the box (.panel-facts, styles/components.css).
 */
function AnswerFacts({ shown, accent }) {
  const count = shown?.results?.length ?? 0
  if (!shown?.corrected?.length && !shown?.read_as && !count) return null
  return (
    <div className="panel-facts">
      <CorrectedNote corrected={shown.corrected} />
      <ReadAsNote readAs={shown.read_as} />
      {count > 0 && (
        /* One is the usual answer for a whole Arabic word, the dictionary is
           indexed by headword, but a part-word, a spaced root, or an English
           search all come back with several. */
        <p className="type-small text-[var(--text-dim)]">{count === 1 ? '1 entry' : `${count} entries`}</p>
      )}
      {/* The classical books sit under every word card, three or four screens
          down on a phone; this is the way to them without the scroll. */}
      {count > 0 && shown.lang === 'ar' && (
        <button
          type="button"
          onClick={() => scrollToEl(document.getElementById(CLASSICAL), 'top')}
          style={{ '--c': accent }}
          className="tap type-small text-[var(--text-faint)] hover:text-[var(--c)] transition-colors"
        >
          Classical dictionaries ↓
        </button>
      )}
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
  // No frame round the books at all: a section under a small label, like the
  // words on the root above it. Three borders deep, then one, the page still
  // read as boxes before it read as dictionaries.
  return (
    <section
      id={CLASSICAL}
      aria-labelledby={`${CLASSICAL}-h`}
      className="flex flex-col gap-4 scroll-mt-24"
    >
      <header className="flex items-center gap-x-3 gap-y-2 flex-wrap">
        <h3 id={`${CLASSICAL}-h`} className="eyebrow">Classical dictionaries</h3>
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
        <ChipRow scroll role="group" aria-label="Which book">
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
