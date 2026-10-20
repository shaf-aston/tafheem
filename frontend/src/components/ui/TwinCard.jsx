/**
 * The twins of one ayah: each partner verse laid under this one, so the eye
 * goes straight to the words that tell them apart.
 *
 * Shared words stay quiet; differing words take the tab accent. The states are
 * the page's usual ones, so the panel and the kit page draw the same thing.
 */
import { wordsOf } from '../../lib/memorise'
import { placeLine, wordFlags } from '../../lib/similar'
import { smartError } from '../../lib/apiError'

import ArabicText from './ArabicText'
import EmptyState from './EmptyState'
import ErrorAlert from './ErrorAlert'
import RetryButton from './RetryButton'
import { Skeleton } from './Skeleton'
import SourceBadge from './SourceBadge'

/** One verse as a row of words, the differing ones in the accent. */
function TwinRow({ label, words, spans, accent }) {
  const flags = wordFlags(words.length, spans)
  return (
    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1" dir="rtl">
      {words.map((word, w) => (
        <ArabicText
          key={w}
          size="base"
          className={flags[w] ? undefined : 'text-[var(--text-dim)]'}
          style={flags[w] ? { color: accent } : undefined}
        >
          {word}
        </ArabicText>
      ))}
      <span className="type-small text-[var(--text-faint)] shrink-0">{label}</span>
    </div>
  )
}

export function TwinCard({ mine, partner, accent }) {
  return (
    <article className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-3 space-y-2">
      <TwinRow label={mine.key} words={wordsOf(mine.text)} spans={partner.diff_self} accent={accent} />
      <TwinRow label={partner.key} words={wordsOf(partner.text)} spans={partner.diff_other} accent={accent} />
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="type-small text-[var(--text-dim)]">
          {placeLine(mine.key, partner.key)}
          {partner.change_type && ` (${partner.change_type})`}
        </p>
        <span className="flex gap-1">{partner.sources.map((s) => <SourceBadge key={s.label} source={s} />)}</span>
      </div>
    </article>
  )
}

/** All the cards for one ayah, or its loading, empty or error state. `query` is a react-query result. */
export default function TwinCards({ mine, query, accent }) {
  const { data, isPending, isError, error, refetch } = query
  if (isPending) return <Skeleton className="h-24 w-full" />
  if (isError) {
    return (
      <ErrorAlert title="Similar verses could not be read">
        {smartError(error, 'They come from the Qur\'an tab\'s own source.')}
        <RetryButton onClick={refetch} />
      </ErrorAlert>
    )
  }
  if (!data?.partners?.length) return <EmptyState>No similar verses recorded for this ayah.</EmptyState>
  return (
    <div className="space-y-2">
      {data.partners.map((partner) => (
        <TwinCard key={partner.key} mine={mine} partner={partner} accent={accent} />
      ))}
    </div>
  )
}
