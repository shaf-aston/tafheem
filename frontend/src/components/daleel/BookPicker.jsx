/**
 * Which books to search: a shelf of them, or the books themselves.
 *
 * Daleel searches every book at once and hands back a page of results spread
 * across them, so a book with an answer can sit below the fold while another
 * book's answer is on screen. That is fine when the reader is asking the
 * library a question and wrong when they are asking one book, or one shelf of
 * it, which is the ordinary case in fiqh: they want what the Hanafi books say,
 * not what anyone says.
 *
 * Two columns, because there are two ways a person arrives. One knows the book
 * and types its name. The other knows only the subject, and pressing Fiqh puts
 * every fiqh book into the search without their having to know which books
 * those are. A shelf on its own means all of it; naming books means those
 * books, wherever they sit. The shelf and the filter box only decide what is
 * listed, never what is chosen, so a fiqh book and a nahw book can be asked
 * together and typing a title finds it from any shelf.
 *
 * The shelves are data, not code: `category` in data/sources.json. Adding
 * hadith is a line there, and this file never learns their names. Tajweed
 * arrived that way and cost this file nothing.
 *
 * Choosing nothing searches everything, and it says so in words. An empty
 * filter that looked the same as a full one would leave the reader guessing
 * whether their last search covered the library or one corner of it.
 *
 * Open while the page has nothing else on it. Folded under a "Which books"
 * bar it hid the one thing there to look at and cost a click to reach it.
 * Once answers are on screen (`folded`) the list steps aside to its one line:
 * open, the shelf row and the list put the first passage below the fold of
 * a laptop, and the shelf row over the results already says where they are.
 * The line still says what is searched ("all 47 books", "3 books"), opens
 * the list again in one press, and carries the way back to the whole library.
 */
import { useEffect, useMemo, useState } from 'react'

import { nameMatches } from '../../lib/daleel/bookSearch'
import { isArabic } from '../../lib/text/arabicText'

import ArabicText from '../ui/text/ArabicText'
import Chip from '../ui/inputs/Chip'
import ChipRow from '../ui/inputs/ChipRow'

// Not a shelf, the absence of one. A name no category can have, so a shelf
// called "All books" could never collide with it.
const EVERY = '__all__'

/** The shelves, in the order their books arrive, each with how many it holds. */
function shelves(books) {
  const counted = new Map()
  books.forEach(({ category }) => {
    if (category) counted.set(category, (counted.get(category) ?? 0) + 1)
  })
  return [...counted.entries()]
}

/**
 * The books to list. A shelf narrows the list only while the box is empty:
 * once a name is being typed the whole library answers, because a reader who
 * knows the book's name should not have to know its subject first. Scoping the
 * box to the shelf meant typing a Nahw title while Fiqh was on screen found
 * nothing, and read as "we do not have that book".
 */
function matching(books, category, typed) {
  const shelved = typed || category === EVERY ? books : books.filter((b) => b.category === category)
  return shelved.filter((book) => nameMatches(book, typed))
}

export default function BookPicker({ books, onChange, accent, sourceLabel, folded = false }) {
  const [category, setCategory] = useState(EVERY)
  // Opened by hand while answers are on screen; a new set of answers folds it again.
  const [open, setOpen] = useState(false)
  const [wasFolded, setWasFolded] = useState(folded)
  if (folded !== wasFolded) {
    setWasFolded(folded)
    if (folded) setOpen(false)
  }
  const listShown = !folded || open
  const [chosen, setChosen] = useState([])
  const [typed, setTyped] = useState('')

  const listed = useMemo(() => matching(books, category, typed), [books, category, typed])
  const shelfHolds = useMemo(
    () => books.filter((book) => book.category === category).map((book) => book.name),
    [books, category],
  )

  // What the search is actually narrowed to. Named books win; a shelf with no
  // book named means the whole shelf; neither means the whole library. Worked
  // out here and handed over, rather than worked out again by the panel, so the
  // sentence on screen and the search underneath cannot disagree.
  const asked = chosen.length ? chosen : category === EVERY ? [] : shelfHolds
  const key = asked.join('|')

  useEffect(
    () => onChange(key ? key.split('|') : []),
    // The list is compared by its contents, not by its identity: a new array
    // holding the same books is the same request and must not re-run a search.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [key],
  )

  if (books.length === 0) return null

  const toggle = (name) =>
    setChosen((was) => (was.includes(name) ? was.filter((n) => n !== name) : [...was, name]))

  // A shelf changes which books are listed, never which are chosen. Clearing
  // the chosen books here made a cross-subject search impossible: picking
  // القدوري and then stepping to Nahw for الآجرومية silently dropped القدوري,
  // and the reader had no way to ask both books at once. The chips above the
  // list are where a book is taken back out.
  const pickShelf = setCategory

  const clear = () => {
    setCategory(EVERY)
    setChosen([])
    setTyped('')
  }

  const narrowed = chosen.length > 0 || category !== EVERY
  const summary =
    chosen.length
      ? `${chosen.length} book${chosen.length === 1 ? '' : 's'}`
      : category === EVERY
        ? `all ${books.length} books`
        : category

  return (
    <section aria-label="Which books" className="space-y-2">
      <div className="flex items-baseline gap-2 min-w-0">
        <span className="type-small text-[var(--text-faint)] truncate">Searching {summary}</span>
        {/* Beside the summary, so undoing a filter is one click from the line
            that says it is on. */}
        {folded && (
          <button
            type="button"
            onClick={() => setOpen(!open)}
            aria-expanded={open}
            className="type-small shrink-0 px-2 py-0.5 rounded-[var(--radius-sm)]
              border border-[var(--border)] text-[var(--text-dim)]
              hover:text-[var(--text)] hover:border-[var(--border-hi)] transition-colors"
          >
            {open ? 'Hide books' : 'Choose books'}
          </button>
        )}
        {narrowed && (
          <button
            type="button"
            onClick={clear}
            className="type-small shrink-0 ms-auto px-2 py-0.5 rounded-[var(--radius-sm)]
              border border-[var(--border)] text-[var(--text-faint)]
              hover:text-[var(--text)] hover:border-[var(--border-hi)] transition-colors"
          >
            Search all books
          </button>
        )}
      </div>
      {chosen.length > 0 && (
        <ul className="flex flex-wrap gap-1.5">
          {chosen.map((name) => (
            <li key={name}>
              <Chip
                accent={accent}
                selected
                tinted
                arabic={isArabic(name)}
                title="Stop searching this book"
                onClick={() => toggle(name)}
              >
                {name} ✕
              </Chip>
            </li>
          ))}
        </ul>
      )}

      {listShown && <>
      {/* The subjects. A short list that does not grow with the library, so
          it is shown rather than typed for; the books under it are the long
          list and have the box. One scrolling row of chips, as the shelves over
          the results are, so on a phone it costs one line rather than six. */}
      <ChipRow scroll role="group" aria-label="Which subject">
        {[[EVERY, books.length], ...shelves(books)].map(([name, count]) => (
          // Tinted, so the chosen subject is filled and not only recoloured: an
          // outline in another colour was the one sign of which was on.
          <Chip key={name} selected={category === name} tinted accent={accent} onClick={() => pickShelf(name)}>
            <span className="whitespace-nowrap">{name === EVERY ? 'All books' : name} {count}</span>
          </Chip>
        ))}
      </ChipRow>

      <div className="rounded-[var(--radius-md)] overflow-hidden border border-[var(--border)]">
        <div className="bg-[var(--surface)] p-1 space-y-1">
          <input
            type="text"
            value={typed}
            onChange={(event) => setTyped(event.target.value)}
            aria-label="Search the list of books"
            autoComplete="off"
            placeholder="Quduri, الآجرومية, Wiktionary…"
            dir={isArabic(typed) ? 'rtl' : 'ltr'}
            lang={isArabic(typed) ? 'ar' : 'en'}
            style={{ '--c': accent }}
            className={`w-full rounded-[var(--radius-sm)] px-2 py-1.5 text-sm
              bg-[var(--bg)] border border-[var(--border)] text-[var(--text)]
              placeholder:text-[var(--text-faint)] focus:border-[var(--c)]
              focus:outline-none transition-colors
              ${isArabic(typed) ? 'arabic-lg text-right' : ''}`}
          />
          <p className="type-small text-[var(--text-faint)] px-1">
            {typed && category !== EVERY
              ? `Looking through all ${books.length} books, not just ${category}`
              : 'Type to narrow the list, click a book to add it'}
          </p>

          {/* Two columns once there is room: the library is long enough that a
              single column buries half of it below the scroll. On a narrow
              screen it stays one column, where two would squeeze the names. */}
          {/* The fade signals more rows below the clip rather than letting a
              name look cut off mid-letter. */}
          <div className="relative">
          <ul className="max-h-40 sm:max-h-52 overflow-y-auto sm:grid sm:grid-cols-2 sm:gap-x-1">
            {listed.length === 0 ? (
              <li className="px-2 py-1.5 type-small text-[var(--text-faint)]">
                No book here is called that.
              </li>
            ) : (
              listed.map((book) => (
                <li key={book.name}>
                  <button
                    type="button"
                    onClick={() => toggle(book.name)}
                    aria-pressed={chosen.includes(book.name)}
                    style={{ '--c': accent }}
                    className={`w-full text-start px-2 py-1.5 rounded-[var(--radius-sm)]
                      flex items-baseline justify-between gap-3 transition-colors
                      hover:bg-[var(--surface-hi)]
                      ${chosen.includes(book.name) ? 'text-[var(--c)]' : 'text-[var(--text)]'}`}
                  >
                    {/* The English name under the Arabic one, where the book
                        has both. A name a reader cannot see is a name they have
                        to guess at, and the box above them invites them to type
                        exactly this. Never instead of the Arabic: that is what
                        the book calls itself and what the quotation is filed
                        under. Its line is kept even when the book has no
                        English name, so the rows either side of it stay level;
                        see .book-name in styles/components.css. */}
                    <span className="min-w-0">
                      {isArabic(book.name) ? (
                        /* Right-to-left letters, left-aligned box. The name
                           reads as Arabic; the row it sits in is an English
                           list, and a name that hugged the right edge would
                           start in a different place on every row, since the
                           box is only as wide as the English under it. */
                        <ArabicText as="div" size="sm" className="book-name text-left">
                          {book.name}
                        </ArabicText>
                      ) : (
                        <div className="book-name text-sm">{book.name}</div>
                      )}
                      <div className="book-sub type-small text-[var(--text-faint)]" dir="ltr">
                        {book.english}
                      </div>
                    </span>
                    {/* Which badge it will appear under, so a reader who knows
                        the tab by its badges can find a book by its badge. Left
                        off where the source is that one book: printing its name
                        twice on one line says there are two things here. */}
                    {sourceLabel(book.source) !== book.name && (
                      <span className="type-small text-[var(--text-faint)] shrink-0">
                        {sourceLabel(book.source)}
                      </span>
                    )}
                  </button>
                </li>
              ))
            )}
          </ul>
          <div
            aria-hidden="true"
            className="pointer-events-none absolute bottom-0 inset-x-0 h-6"
            style={{ background: 'linear-gradient(to bottom, transparent, var(--surface))' }}
          />
          </div>
        </div>
      </div>
      </>}
    </section>
  )
}
