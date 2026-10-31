/**
 * The hadith one narrator is in the chain of, found the way a reader looks for
 * one: which collection, then which book, then the hadith itself by what it says.
 *
 * It was one flat list, "Bukhari 9", "Bukhari 14" and on for thousands of rows
 * (Abu Hurayra is in over four thousand): numbers no reader goes by. Now a pill
 * per collection with its count, under it that collection's first books by name, each
 * shut until opened, and only an opened book draws its rows. A row gives the
 * English (the words after "Narrated X:", from the book the reader opens anyway)
 * beside the Arabic opening, as sunnah.com sets a hadith: English left, Arabic right.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { hadithBookQuery, hadithBooksQuery } from '../../../api'
import { narrated } from '../../../lib/hadith/hadithWords'
import { useHadithCollections } from '../useHadithCollections'

import ArabicText from '../../ui/text/ArabicText'
import Chip from '../../ui/inputs/Chip'
import ChipRow from '../../ui/inputs/ChipRow'
import Disclosure from '../../ui/overlays/Disclosure'
import { FoldedList, PAIR_ROWS } from './NarratorParts'

/** Rows by collection, then by book, both in the order the server sent them (the tab's order, then number). */
function grouped(rows) {
  const out = new Map()
  for (const row of rows) {
    const books = out.get(row.collection) ?? out.set(row.collection, new Map()).get(row.collection)
    books.set(row.book, [...(books.get(row.book) ?? []), row])
  }
  return out
}

export default function NarratorHadith({ rows, total, accent, onHadith }) {
  const { of } = useHadithCollections()
  const collections = grouped(rows)
  const [picked, setPicked] = useState(null)
  const current = collections.has(picked) ? picked : collections.keys().next().value

  return (
    <div className="space-y-3">
      <ChipRow>
        {[...collections].map(([id, books]) => (
          <Chip key={id} accent={accent} tinted selected={id === current} onClick={() => setPicked(id)}>
            {of(id).short} <span className="tabular-nums opacity-70">{[...books.values()].reduce((n, list) => n + list.length, 0)}</span>
          </Chip>
        ))}
      </ChipRow>
      {/* Keyed, so another collection's books open shut. */}
      <Books key={current} collection={current} books={collections.get(current)} accent={accent} onHadith={onHadith} />
      {total > rows.length && <p className="type-small text-[var(--text-faint)] m-0">Showing the first {rows.length} of {total}.</p>}
    </div>
  )
}

function Books({ collection, books, accent, onHadith }) {
  // Prefetched with the tab, so the names are usually here already; a number stands in till they are.
  const { data: names = [] } = useQuery(hadithBooksQuery(collection))
  // Abu Hurayra is in 85 of Bukhari's books: the first few, the rest a press away, as his teachers are.
  return (
    <FoldedList items={[...books]} accent={accent} noun="books">
      {(shown) => (
        <div className="space-y-2 mb-2">
          {shown.map(([book, list], i) => (
            <Book key={book} index={i} collection={collection} book={book} name={names.find((b) => b.number === book)} rows={list} accent={accent} onHadith={onHadith} />
          ))}
        </div>
      )}
    </FoldedList>
  )
}

function Book({ index, collection, book, name, rows, accent, onHadith }) {
  // Drawn once first opened and kept, so shutting it glides rather than empties.
  const [seen, setSeen] = useState(false)
  return (
    <div className="rise-in" style={{ '--i': Math.min(index, 8) }}>
      <Disclosure
        framed
        onToggle={(open) => open && setSeen(true)}
        bodyClassName="px-4"
        label={(
          <span className="flex items-baseline gap-3 min-w-0">
            <span className="tabular-nums text-[var(--text-faint)] min-w-[2ch]">{book}</span>
            <span className="min-w-0 flex-1 truncate type-ui text-[var(--text)]">{name?.name ?? `Book ${book}`}</span>
            {name?.arabic && <ArabicText size="sm" className="hidden sm:inline text-[var(--text-faint)] truncate">{name.arabic}</ArabicText>}
            <span className="type-small tabular-nums text-[var(--text-faint)] whitespace-nowrap">{rows.length}</span>
          </span>
        )}
      >
        {seen && <Rows collection={collection} book={book} rows={rows} accent={accent} onHadith={onHadith} />}
      </Disclosure>
    </div>
  )
}

function Rows({ collection, book, rows, accent, onHadith }) {
  // The book the reader lands in on a tap: fetched now, it is what gives each row its English.
  const { data } = useQuery(hadithBookQuery(collection, book))
  // One lookup per book, not a search of it per row. A missing part is '' on one side and null on the other.
  const english = new Map(data?.hadiths.map((x) => [`${x.number}${x.part ?? ''}`, narrated(x.english).body]))
  return (
    <ul className={PAIR_ROWS}>
      {rows.map((h) => {
        const ref = `${h.number}${h.part ?? ''}`
        return (
          <li key={ref}>
            <button
              type="button"
              onClick={() => onHadith(h)}
              style={{ '--c': accent }}
              className="press w-full text-start py-3 flex items-baseline gap-3 group hover:bg-[var(--surface)] transition-colors"
            >
              <span className="type-small tabular-nums text-[var(--text-faint)] group-hover:text-[var(--c)] min-w-[3ch] transition-colors">{ref}</span>
              <span className="min-w-0 flex-1 grid gap-x-6 gap-y-1 md:grid-cols-2">
                {/* A line held for the English while the book comes, so the row does not jump. */}
                {!data && <span className="skeleton block h-4 w-3/4" />}
                {english.get(ref) && <span className="type-small text-[var(--text)] line-clamp-2">{english.get(ref)}</span>}
                <ArabicText size="sm" className="block line-clamp-2 text-[var(--text-dim)]">{h.opening}</ArabicText>
              </span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
