/**
 * The twins of one ayah: each partner verse laid under this one, so the eye
 * goes straight to the words that tell them apart.
 *
 * Shared words stay quiet; differing words take the tab accent. The states are
 * the page's usual ones, so the panel and the kit page draw the same thing.
 */
import { wordsOf } from '../../../lib/memorise/memorise'
import { flagsOnPage, placeLine, wordFlags } from '../../../lib/similar/similar'
import copy from '../../../config/similar.json'

import ArabicText from './ArabicText'
import EmptyState from '../feedback/EmptyState'
import ErrorAlert from '../feedback/ErrorAlert'
import { Skeleton } from '../feedback/Skeleton'
import SourcesChip from '../feedback/SourcesChip'

/** One verse as a row of words, the differing ones in the accent. Similar verses' Compare draws its verses with it too. */
export function TwinRow({ label, words, flags, accent }) {
  return (
    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1" dir="rtl">
      {words.map((word, w) => (
        <ArabicText
          key={w}
          size="base"
          // The shared words sink back and the differing ones pulse once, so the
          // eye lands on what differs (twin-same, twin-diff in motion.css).
          className={flags[w] ? 'twin-diff' : 'twin-same text-[var(--text-dim)]'}
          style={flags[w] ? { color: accent } : undefined}
        >
          {word}
        </ArabicText>
      ))}
      <span className="type-small text-[var(--text-faint)] shrink-0">{label}</span>
    </div>
  )
}

function TwinCard({ mine, text, partner, accent }) {
  const mineWords = wordsOf(mine.text)
  const theirWords = wordsOf(partner.text)
  return (
    <article className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-3 space-y-2">
      <TwinRow label={mine.key} words={mineWords} flags={flagsOnPage(mineWords, text, partner.diff_self)} accent={accent} />
      <TwinRow label={partner.key} words={theirWords} flags={wordFlags(theirWords.length, partner.diff_other)} accent={accent} />
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="type-small text-[var(--text-dim)]">
          {placeLine(mine.key, partner.key)}
          {partner.change_type && ` (${partner.change_type})`}
        </p>
        <SourcesChip sources={partner.sources} align="end" />
      </div>
    </article>
  )
}

/** All the cards for one ayah, or its loading, empty or error state. `query` is a react-query result. */
export default function TwinCards({ mine, query, accent }) {
  const { data, isPending, isError, error, refetch } = query
  if (isPending) return <Skeleton className="h-24 w-full" />
  // The Similar tab's own words and ErrorAlert's own reason and retry, so the
  // same failure never reads two ways.
  if (isError) return <ErrorAlert title={copy.error} error={error} fallback={copy.fallback} onRetry={refetch} />
  if (!data?.partners?.length) return <EmptyState>No similar verses recorded for this ayah.</EmptyState>
  return (
    <div className="space-y-2">
      {data.partners.map((partner) => (
        <TwinCard key={partner.key} mine={mine} text={data.text} partner={partner} accent={accent} />
      ))}
    </div>
  )
}
