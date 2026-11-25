/**
 * A quotation read where it stands: the passages before and after it in the
 * same book, in the book's order, the chosen one boxed and the rest quieter.
 *
 * A line lifted out of a chapter can say the opposite of the chapter, so this
 * lets a reader check before citing it. Neighbours never cross into another
 * book (index/around); the citation sits at the foot with a copy button.
 */
import { useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'

import { daleelAroundQuery } from '../../api'
import BottomSheet from '../ui/overlays/BottomSheet'
import CloseButton from '../ui/buttons/CloseButton'
import CopyButton from '../ui/buttons/CopyButton'
import ErrorAlert from '../ui/feedback/ErrorAlert'
import StatusNote from '../ui/feedback/StatusNote'
import { AnalyzerSkeleton } from '../ui/feedback/Skeleton'
import Passage from './Passage'
import { citeOf } from './cite'
import settings from '../../config/daleel.json'

// A saved passage keeps its number; after a rebuild that number can belong to another passage.
const same = (a, b) => a.id === b.id && a.locator === b.locator && a.book === b.book

export default function ContextSheet({ hit, accent, onClose }) {
  const { data: passages, isPending, isError, error, refetch } = useQuery(daleelAroundQuery(hit.id))
  const title = hit.book || hit.source?.label || 'In context'
  const found = passages?.some((p) => same(p, hit))
  // The chosen passage opens in view: three neighbours above it filled the sheet.
  const showChosen = useCallback((node) => node?.scrollIntoView({ block: 'center' }), [])

  return (
    <BottomSheet label={`${title}, in context`} onClose={onClose} className="max-h-[var(--sheet-tall)] flex flex-col">
      <header className="flex items-center justify-between gap-3 px-5 pt-4 pb-3">
        <h2 className="type-ui font-semibold text-[var(--text)]">{title}</h2>
        <CloseButton onClick={onClose} className="shrink-0" />
      </header>

      <div className="overflow-y-auto px-5 pb-4 space-y-4">
        {isPending && <AnalyzerSkeleton />}
        {/* One book per sheet, so its English is labelled once, not on every passage. */}
        {found && settings.glossed.includes(hit.source?.key) && (
          <p className="type-small text-[var(--text-faint)]">{settings.glossNote}</p>
        )}
        {isError && <ErrorAlert title="Could not open the book here" error={error} onRetry={refetch} />}
        {passages && !found && (
          <StatusNote>This book has changed since the passage was saved. Search for it again to read it in context.</StatusNote>
        )}
        {found && passages.map((p) => {
          const chosen = same(p, hit)
          // The chosen one carries the marks its search found; its neighbours were not searched.
          const shown = chosen ? hit : p
          return (
            <article
              key={p.id}
              ref={chosen ? showChosen : undefined}
              aria-current={chosen || undefined}
              style={{ '--c': accent }}
              className={chosen
                ? 'rounded-[var(--radius-md)] border border-[var(--c)] p-4 space-y-2'
                : 'px-4 space-y-2 opacity-60'}
            >
              <p className="type-small text-[var(--text-faint)] font-mono">{p.locator}</p>
              {/* Base, not the cards' large size: a page of the book is read here, and at large one ayah filled a phone. */}
              {shown.arabic && <Passage text={shown.arabic} marks={shown.arabic_marks} accent={accent} arabic size="base" />}
              {shown.english && <Passage text={shown.english} marks={shown.english_marks} accent={accent} />}
            </article>
          )
        })}
      </div>

      <footer className="flex items-center justify-between gap-3 px-5 py-3 border-t border-[var(--border)]">
        <span className="type-small text-[var(--text-faint)]">{citeOf(hit)}</span>
        <CopyButton text={citeOf(hit)} label="Copy citation" small />
      </footer>
    </BottomSheet>
  )
}
