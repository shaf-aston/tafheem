/**
 * Daleel: find the passage that says it, in the books themselves.
 *
 * One box, asked in Arabic or in English, searched across every installed book
 * at once. It quotes; it does not rule. Every hit carries the book it came
 * from, where in that book it sits, and how the match was made, because a
 * passage without its place is an assertion rather than evidence.
 *
 * Which books are searched is a filter on the answer, not a different
 * question: narrowing re-asks the same question straight away rather than
 * leaving passages on screen from books the reader has just excluded.
 */
import { useState } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { daleelBooksQuery, findDaleel } from '../api'
import settings from '../daleel.json'
import { isArabic, mostlyArabic } from '../lib/arabicText'
import { isAyah } from '../lib/surahRef'
import { plainEntry } from '../lib/laneEntry'
import { markedPieces, withMarks } from '../lib/marked'
import { sourcesFor, useSources } from '../lib/useSources'
import { useSearch } from '../lib/useSearch'
import { LANE, LANE_TIDY_LABEL, LANE_TIDY_TITLE, useLaneTidy } from '../lib/useLaneTidy'

import ArabicText from './ui/ArabicText'
import Chip from './ui/Chip'
import ChipRow from './ui/ChipRow'
import Disclosure from './ui/Disclosure'
import BookPicker from './daleel/BookPicker'
import EmptyState from './ui/EmptyState'
import IndexNotBuilt from './ui/IndexNotBuilt'
import LoadMore from './ui/LoadMore'
import Mark from './ui/Mark'
import FlagButton from './ui/FlagButton'
import MicButton from './ui/MicButton'
import PlaceLinks from './ui/PlaceLinks'
import ErrorAlert from './ui/ErrorAlert'
import RecentRow from './ui/RecentRow'
import { GoButton } from './ui/RootActions'
import SearchBox from './ui/SearchBox'
import SectionHeader from './ui/SectionHeader'
import ShowRest from './ui/ShowRest'
import { AnalyzerSkeleton } from './ui/Skeleton'
import SourceBadge from './ui/SourceBadge'

/**
 * How a hit was made, said in the reader's words beside it.
 *
 * An exact hit says nothing: it is what was asked for. The other three are the
 * search quietly widening the question, and a reader who typed one word and is
 * shown another needs to be told which liberty was taken.
 */
const MATCH_NOTE = {
  // Only some of the words asked for. Without a note it read as a clean find.
  partial: 'some of your words',
  loose: 'close spelling',
  root: 'same root',
  related: 'related word',
}

export default function DaleelPanel({ accent, incoming, arrival, onGo, onVisit }) {
  const [laneTidy, setLaneTidy] = useLaneTidy()
  const [chosen, setChosen] = useState([])
  // The shelf the answer is being looked through, for the question it was
  // picked on; a new question starts with every shelf again.
  const [looking, setLooking] = useState({ query: null, shelf: null })

  // A question that came back is a place reached: Recent, the trail, and the
  // address bar all record it. Which books were searched is not in it; that is
  // a filter on the answer, not a different question. See lib/journey.js.
  // An arriving question (another tab, the back arrow) is asked of every book.
  const { query, setQuery, history, mutation, submit: ask, clear, shown: data } = useSearch({
    historyKey: 'daleel-history', ask: findDaleel, onVisit, incoming, arrival,
  })

  // Show more: the same question again with a bigger page. A query of its own,
  // not the search, so Recent and the trail do not count it as a second
  // question, and the page already read stays up while the bigger one loads.
  // Keyed to the books too: narrowing starts again from one page.
  const asked = data && `${data.query}\n${data.books?.join('\n')}`
  const [widened, setWidened] = useState({ asked: null, size: 0 })
  const size = widened.asked === asked ? widened.size : 0
  const bigger = useQuery({
    queryKey: ['daleel', asked, size],
    queryFn: () => findDaleel({ q: data.query, books: data.books, limit: size }),
    enabled: size > 0,
    placeholderData: keepPreviousData,
  })
  const answer = size > 0 && bigger.data && `${bigger.data.query}\n${bigger.data.books?.join('\n')}` === asked
    ? bigger.data : data

  // The list of books to offer. Asked for once and kept: it changes only when
  // the index is rebuilt, which cannot happen while the page is open.
  const { data: catalogue = [] } = useQuery(daleelBooksQuery)

  // No language is sent: one request reads the Arabic and the English index
  // together, which is what makes the single box honest.
  const submit = (given, books = chosen) => ask(given, { books })

  // Changing which books are searched re-asks the same question straight away.
  // Leaving the old results on screen under a new filter would show passages
  // from books the reader had just excluded, which is the one thing this
  // control must never do. The books are passed rather than read back, because
  // the state has not settled by the time this runs.
  const narrow = (books) => {
    setChosen(books)
    if (mutation.data || mutation.isError) submit(undefined, books)
  }

  // The books come in one order every time, taken from sources.json rather
  // than from how well this particular search happened to go. A page whose
  // sections move around between searches cannot be learned.
  const { sources } = useSources()
  // Stale results under a spinner is a state a reader has no way to name; the
  // skeleton fully replaces them instead of sitting on top, except through a
  // return (lib/useSearch).
  const hits = inBookOrder(answer?.hits ?? [], sourcesFor(sources, 'daleel'))
  // Each book's shelf (Qur'an, Tafsir, Dictionary…), as the catalogue files it.
  const shelfOf = new Map(catalogue.map((book) => [book.source, book.category]))
  const shelves = countShelves(hits, shelfOf)
  const shelf = looking.query === data?.query ? looking.shelf : null
  const seen = shelf ? hits.filter((hit) => shelfOf.get(hit.source?.key) === shelf) : hits
  // Of what is on show, so the line agrees with the cards under it once a shelf is picked.
  const passageCount = seen.length
  const bookCount = new Set(seen.map(bookOf)).size
  // What was asked for first; the search widening the question (a close
  // spelling, the root, a related word) folds under it, so a looser match
  // never takes the room of a quotation.
  const exact = seen.filter((hit) => !MATCH_NOTE[hit.match])
  const looser = seen.filter((hit) => MATCH_NOTE[hit.match])
  const anyLane = hits.some((hit) => bookOf(hit) === LANE)
  const card = (hit) => (
    <li key={`${bookOf(hit)}-${hit.locator}`}>
      <Quotation hit={hit} onGo={onGo} accent={accent} tidy={bookOf(hit) === LANE && laneTidy} />
    </li>
  )

  return (
    <div className="panel">
      <SectionHeader tab="daleel"
        subtitle="Searchable in Arabic or in English. It quotes the books; it does not rule."
      />

      {/* Every recent question, whichever language it was asked in, each chip
          set in its own script. They used to be split into two lists by the
          toggle above, so half of them were hidden at any one time. */}
      {/* Until anything has been asked, the same row offers questions to try,
          so the empty page says what it can be asked. */}
      <RecentRow
        items={history.length ? history.map((h) => h.q) : settings.examples}
        label={history.length ? 'Recent' : 'Try'}
        accent={accent}
        onPick={submit}
      />

      <div className="space-y-3">
        {/* The same field as the Dictionary and the Quran tabs, down to the
            keycap and the microphone: three tabs that take a question should
            not take it three different ways. See ui/SearchBox. */}
        <SearchBox
          id="daleel-input"
          label="Arabic or English"
          hint="Enter to search, or say it"
          placeholder="الصبر or patience"
          value={query}
          onChange={setQuery}
          onSubmit={submit}
          onClear={clear}
          busy={mutation.isPending}
          accent={accent}
        >
          {/* Speaking a phrase, not an ayah: Daleel searches whatever words come
              back, so it asks only for those and never for a list of ayahs. */}
          <MicButton
            onHeard={({ text }) => { setQuery(text); mutation.reset() }}
            accent={accent}
            title="Say what you are looking for"
          />
        </SearchBox>

        {/* Below the search box, not above: most searches want the whole
            library, so the box that everyone uses leads and the filter, which
            is the occasional case, sits under it. See daleel/BookPicker. */}
        <BookPicker
          books={catalogue}
          folded={hits.length > 0}
          onChange={narrow}
          accent={accent}
          sourceLabel={(key) => sources.find((s) => s.key === key)?.label ?? key}
        />
      </div>

      <PlaceLinks query={query} onGo={onGo} accent={accent} />

      {mutation.isError && (
        <ErrorAlert title="Search failed" error={mutation.error} fallback="Could not reach the backend." onRetry={() => submit()} />
      )}

      {data?.ready === false && <IndexNotBuilt command="python backend/scripts/build_daleel_index.py" />}

      {/* With a filter on, the sentence has to name the limit. "Nothing in the
          books" while nine books out of ten were excluded is a claim about the
          whole library that the search never made. */}
      {data?.ready !== false && data && data.hits.length === 0 && (
        <EmptyState>
          {data.books?.length
            ? `Nothing in ${data.books.length === 1 ? 'that book' : 'those books'}`
              + ` matches “${data.query}”.`
              + ' The rest of the library has not been searched.'
            : `Nothing in the books matches “${data.query}”.`}
          {' '}{settings.tries}
        </EmptyState>
      )}

      {/* The live region is this one sentence, not the whole results block: with
          the block itself announced, every passage in it got read aloud. */}
      <p className="sr-only" role="status" aria-live="polite">
        {data ? `${passageCount} passages in ${bookCount} books` : ''}
      </p>

      {mutation.isPending && !data && <AnalyzerSkeleton />}

      {hits.length > 0 && (
        <div className="space-y-3">
          {/* The answer at a glance: how much came back, and from which shelves,
              each a press away from being all that is shown. */}
          <div className="flex items-center gap-3">
            <p className="type-small text-[var(--text-faint)]">
              {passageCount} {passageCount === 1 ? 'passage' : 'passages'} · {bookCount} {bookCount === 1 ? 'book' : 'books'}
            </p>
            {/* Only Lane carries the scholar's marks, so the switch shows only with him. */}
            {anyLane && (
              <div className="ms-auto">
                <FlagButton value={laneTidy} onChange={setLaneTidy} accent={accent} title={LANE_TIDY_TITLE}>
                  {LANE_TIDY_LABEL}
                </FlagButton>
              </div>
            )}
          </div>
          {shelves.length > 1 && (
            <ChipRow scroll role="group" aria-label="Show one shelf">
              {[[null, hits.length], ...shelves].map(([name, count]) => (
                <Chip key={name ?? 'all'} selected={shelf === name} accent={accent}
                  onClick={() => setLooking({ query: data.query, shelf: name })}>
                  <span className="whitespace-nowrap">{name ?? 'All'} {count}</span>
                </Chip>
              ))}
            </ChipRow>
          )}

          {exact.length > 0 && <ul className="space-y-3">{exact.map(card)}</ul>}
          {looser.length > 0 && (
            <Disclosure key={`${data.query} ${shelf}`} defaultOpen={exact.length === 0}
              label={`${looser.length} looser ${looser.length === 1 ? 'match' : 'matches'}`}>
              <ul className="space-y-3 pt-3">{looser.map(card)}</ul>
            </Disclosure>
          )}
          {answer.more && (
            <LoadMore busy={bigger.isFetching}
              onClick={() => setWidened({ asked, size: answer.hits.length + settings.more })} />
          )}
        </div>
      )}
    </div>
  )
}

/**
 * One passage, exactly as its book has it.
 *
 * The Arabic is first and large because it is the thing that was asked for.
 * The address sits quietly at the foot: a quotation with no address is a
 * rumour, but it is not what the eye should land on first.
 */
function Quotation({ hit, onGo, accent, tidy }) {
  const note = MATCH_NOTE[hit.match]
  const ayah = ayahIn(hit.locator)
  const [open, setOpen] = useState(false)
  const [cut, setCut] = useState(false)
  // A press anywhere on a cut card opens all of it. Not a press on one of its
  // own controls, and not the end of a drag that selected some of the text.
  const openFromCard = (event) => {
    if (!cut || open || event.target.closest('a, button')) return
    if (!(window.getSelection()?.isCollapsed ?? true)) return
    setOpen(true)
  }

  return (
    <article
      // The accent is set here, not inherited: it was read off the search box,
      // which is a different subtree, so the hover below resolved to nothing.
      style={{ '--c': accent }}
      onClick={openFromCard}
      className={`rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)]
        p-4 sm:p-5 space-y-3 ${cut && !open ? 'cursor-pointer' : ''}`}
    >
      {/* Whose words, and where in the book, at the head of the card: a heading
          of its own over every book cost a row per passage. */}
      <header className="flex items-center gap-2 flex-wrap">
        <SourceBadge source={hit.source} />
        {/* A dictionary entry is cited by the word itself, which is already the
            quotation below. Printing it again said nothing. */}
        <Locator text={hit.locator === hit.arabic ? '' : hit.locator} />
        {/* Set apart from the quiet citation beside it: the one line that stops
            a probable typo-fix from reading as a clean find. */}
        {note && (
          <span className="ms-auto type-small px-2 py-0.5 rounded-full border"
            style={{ color: 'var(--warn)', borderColor: 'var(--warn-edge)' }}>
            {note}
          </span>
        )}
      </header>

      {/* One fold for the whole passage: a press on the card, or on Show all,
          opens the Arabic and the English together. */}
      <ShowRest height="var(--daleel-passage-h)" accent={accent}
        open={open} onOpenChange={setOpen} onCutChange={setCut}
        beside={onGo && ayah && (
          <GoButton onClick={() => onGo('quran', ayah)} style={{ '--c': accent }}>
            Open the ayah
          </GoButton>
        )}>
        <div className="space-y-3">
          {hit.arabic && <Passage text={hit.arabic} marks={hit.arabic_marks} accent={accent} tidy={tidy} arabic />}
          {hit.english && <Passage text={hit.english} marks={hit.english_marks} accent={accent} tidy={tidy} />}
        </div>
      </ShowRest>
    </article>
  )
}

/**
 * One side of a passage, cut to a few lines when it runs long.
 *
 * Ibn Kathir's entries are whole pages, and set beside an ayah of six words
 * they turned the results into one card and a wall. The cut is not a
 * shortening: the whole passage is a press away, and no card is allowed to
 * decide the height of the page on its own.
 *
 * Both sides fold, not only the English. Every Arabic text Daleel held was
 * short, so the wall could only ever come from a translation; the unabridged
 * Arabic commentaries average a printed page each and put the same wall in the
 * language the reader asked in.
 *
 * ui/ShowRest measures the overflow rather than counting characters, so a
 * passage that happens to fit grows no button. The character threshold this
 * used to keep called a 330-character line long on a phone and on a desktop
 * alike, where it is four lines and one.
 */
function Passage({ text, marks, accent, tidy = false, arabic = false }) {
  // A dictionary entry arrives with the marks its own dump wrote into it.
  // Every other book passes through untouched, none of them carrying those
  // marks in the first place. The server's marks for the matched words go in
  // first, so they ride through that reshaping and still land on their words.
  const pieces = markedPieces(plainEntry(withMarks(text, marks), { tidy }))
  const said = pieces.map((piece, n) => piece.marked
    ? <Mark key={n} accent={accent}>{piece.text}</Mark>
    : piece.text)

  return arabic && mostlyArabic(pieces.map((piece) => piece.text).join('')) ? (
    <ArabicText size="lg" className="block leading-loose whitespace-pre-line">{said}</ArabicText>
  ) : (
    <p className="type-body text-[var(--text-dim)] leading-relaxed whitespace-pre-line max-w-prose">
      {said}
    </p>
  )
}

const bookOf = (hit) => hit.source?.key ?? 'unknown'

/**
 * Hits in book order, books in the order sources.json lists them, each book's
 * own hits in the order the search returned them.
 *
 * The order is fixed rather than by how well each book scored, because the two
 * differ and the fixed one is the useful one. On a misspelling every book can
 * match about equally well, and ordering by score put a dictionary idiom above
 * al-Fatihah purely because it was the shorter line.
 */
function inBookOrder(hits, order) {
  const rank = new Map(order.map((source, n) => [source.key, n]))
  return hits.map((hit, n) => [hit, n])
    .sort(([a, i], [b, j]) => (rank.get(bookOf(a)) ?? 99) - (rank.get(bookOf(b)) ?? 99) || i - j)
    .map(([hit]) => hit)
}

/** Each shelf the hits are on, in the order they first appear, with how many each holds. */
function countShelves(hits, shelfOf) {
  const counted = new Map()
  for (const hit of hits) {
    const shelf = shelfOf.get(hit.source?.key)
    if (shelf) counted.set(shelf, (counted.get(shelf) ?? 0) + 1)
  }
  return [...counted.entries()]
}

/**
 * The ayah a citation points at, "2:255", or null. A translation or a tafsir
 * cites one after its own name ("Saheeh International 18:68"), so the ayah is
 * read off the end, and only one that is really in the Qur'an counts: a
 * section mark or a root is no place the Quran tab can open.
 */
function ayahIn(locator) {
  const [, surah, ayah] = /(?:^|\s)(\d+):(\d+)$/.exec(locator ?? '') ?? []
  return surah && isAyah({ surah: Number(surah), ayah: Number(ayah) }) ? `${surah}:${ayah}` : null
}

/**
 * Where a passage came from. An ayah reference like 2:45 is a number and reads
 * well in the mono face; a book citation is Arabic, and the mono face has no
 * Arabic in it, so the browser substituted letter by letter and the word came
 * out unjoined. Arabic also has to be marked rtl or a page number lands on the
 * wrong side of its ص.
 */
function Locator({ text }) {
  if (!text) return <span />
  if (isArabic(text)) {
    return (
      <ArabicText size="tiny" className="arabic-inline text-[var(--text-faint)]">
        {text}
      </ArabicText>
    )
  }
  return <span className="type-small text-[var(--text-faint)] font-mono">{text}</span>
}
