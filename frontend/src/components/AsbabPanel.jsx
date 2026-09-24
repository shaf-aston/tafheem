/**
 * Why the ayahs of one moment came down: al-Suyuti's reports, in the side panel.
 *
 * Two states in one panel and no nested opening and shutting. The **list** is
 * every report this event carries, grouped by surah, with a search box once
 * there are enough of them to need one. Choosing one replaces the list with the
 * **report** itself: the ayah as a way into the Qur'an tab, the English, the
 * Arabic under it, and the way back to the list.
 *
 * The list comes from the timelines endpoint, which sends one line each. The
 * report is read from the Qur'an's library like any other book on that ayah, so
 * opening one report never fetches the other four hundred.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getAyahEditions, getTimelineAsbab } from '../api'
import { smartError } from '../lib/apiError'
import { bySurah, matching, needsSearch, quotedWords, reportsIn } from '../lib/asbabList'

import ArabicText from './ui/ArabicText'
import Chip from './ui/Chip'
import EmptyState from './ui/EmptyState'
import ErrorAlert from './ui/ErrorAlert'
import RetryButton from './ui/RetryButton'
import SearchBox from './ui/SearchBox'
import SourceBadge from './ui/SourceBadge'
import TranslationStrip from './ui/TranslationStrip'
import { Skeleton } from './ui/Skeleton'

const HOW = {
  named: 'This report names the event',
  period: 'Filed here by its surah, which came down in this stretch',
}

export default function AsbabPanel({ section, event, accent, chosen, onChoose, onGo }) {
  const [query, setQuery] = useState('')
  const list = useQuery({
    queryKey: ['timeline-asbab', section.id, event.id],
    queryFn: () => getTimelineAsbab(section.id, event.id),
    staleTime: Infinity,
  })

  if (list.isPending) return <Skeleton className="h-24 w-full" />
  if (list.isError) {
    return (
      <ErrorAlert title="Could not load the reports" inline>
        {smartError(list.error, 'The reports could not be reached.')}
        <RetryButton onClick={list.refetch} />
      </ErrorAlert>
    )
  }

  const reports = list.data.reports
  const open = reports.find((report) => report.ref === chosen)
  if (open) {
    return (
      <OneReport
        report={open}
        count={reports.length}
        books={list.data.books}
        source={list.data.source}
        accent={accent}
        onBack={() => onChoose(null)}
        onGo={onGo}
      />
    )
  }

  const shown = matching(reports, query)
  return (
    <section className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-5 space-y-3">
      <header className="flex items-baseline justify-between gap-2 flex-wrap">
        <h4 className="text-sm font-semibold text-[var(--text)]">Why these ayahs came down</h4>
        <span className="type-tiny text-[var(--text-faint)]">
          {reports.length} report{reports.length === 1 ? '' : 's'}
        </span>
      </header>

      {needsSearch(reports.length) && (
        <>
          <SearchBox
            id="asbab-search"
            value={query}
            onChange={setQuery}
            placeholder="Search 2:30 or Badr"
            label="Search the reports"
            accent={accent}
          />
          <div className="flex flex-wrap gap-1">
            {bySurah(reports).map((group) => (
              <Chip key={group.surah} accent={accent} onClick={() => setQuery(String(group.surah))} title={`Only surah ${group.surah}`}>
                {group.surah}. {group.name}
              </Chip>
            ))}
          </div>
        </>
      )}

      {shown.length === 0
        ? <EmptyState>No report matches that.</EmptyState>
        : (
          // One line a report: the ayah and the words it is about. Who narrated
          // it waits in the opened report.
          <ol className="list-none m-0 p-0 max-h-[26rem] overflow-y-auto">
            {bySurah(shown).flatMap((group) => group.reports).map((report) => (
              <li key={report.ref}>
                <button
                  type="button"
                  onClick={() => onChoose(report.ref)}
                  title={report.surah_name}
                  className="flex w-full items-baseline gap-3 text-start px-2 py-2 rounded-[var(--radius-sm)] hover:bg-[var(--surface-hi)]"
                >
                  <span className="w-12 shrink-0 text-sm font-medium tabular-nums" style={{ color: accent }}>{report.ref}</span>
                  <span className="min-w-0 line-clamp-2 text-sm text-[var(--text-dim)]">{quotedWords(report.opening)}</span>
                </button>
              </li>
            ))}
          </ol>
        )}

      <div className="flex items-center justify-between gap-2 flex-wrap pt-1">
        <SourceBadge source={list.data.source} />
        {list.data.unplaced > 0 && (
          <span className="type-tiny text-[var(--text-faint)]">
            {list.data.unplaced} more not tied to one ayah
          </span>
        )}
      </div>
    </section>
  )
}

/** One report, read from the library on demand. */
function OneReport({ report, count, books, source, accent, onBack, onGo }) {
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['asbab-passage', report.ref],
    queryFn: () => getAyahEditions(report.surah, report.ayah, [books.arabic, books.english]),
    staleTime: Infinity,
  })
  const passageOf = (id) => data?.passages?.find((passage) => passage.edition === id)
  const english = reportsIn(passageOf(books.english)?.text)
  const arabic = reportsIn(passageOf(books.arabic)?.text)

  return (
    // The report's own words, then the same report in English under a hairline,
    // the shape the ayah view uses. English first and Arabic after was the
    // machine's order, not a reader's: the book is the evidence, the English is
    // the reading of it, and the credit belongs against the English.
    <section className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
      <div className="p-3 space-y-2">
        <button type="button" onClick={onBack} className="type-small text-[var(--text-faint)] hover:text-[var(--text)]">
          ‹ All {count} report{count === 1 ? '' : 's'}
        </button>

        <div className="flex items-center gap-2 flex-wrap">
          <Chip accent={accent} onClick={() => onGo?.('quran', report.ref)} title="Open this ayah in the Qur'an tab">
            Qur'an {report.ref}
          </Chip>
          <span className="type-tiny text-[var(--text-faint)]">{report.surah_name} · {HOW[report.how]}</span>
        </div>

        {isPending && <Skeleton className="h-24 w-full" />}
        {isError && (
          <ErrorAlert title="Could not load this report" inline>
            {smartError(error, 'The report could not be reached.')}
            <RetryButton onClick={refetch} />
          </ErrorAlert>
        )}

        {arabic.map((text, i) => (
          <ArabicText key={`ar-${i}`} size="sm" className="block text-[var(--text)] leading-loose whitespace-pre-line">
            {text}
          </ArabicText>
        ))}
      </div>

      {english.length > 0 && (
        <TranslationStrip source={source} pad="p-3">
          <div className="space-y-2">
            {english.map((text, i) => (
              <div key={`en-${i}`} className="space-y-1">
                {english.length > 1 && (
                  <p className="type-tiny font-semibold" style={{ color: accent }}>
                    Report {i + 1} of {english.length}
                  </p>
                )}
                <p className="text-sm text-[var(--text-dim)] leading-snug whitespace-pre-line">{text}</p>
              </div>
            ))}
          </div>
        </TranslationStrip>
      )}

      {!isPending && english.length === 0 && (
        <TranslationStrip source={source} pad="p-3">
          <p className="type-small text-[var(--text-faint)]">
            No English for this report yet. The book’s own words are above.
          </p>
        </TranslationStrip>
      )}
    </section>
  )
}
