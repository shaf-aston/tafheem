import { verbClass } from '../../lib/sarf/verbClass'

import { Skeleton } from '../ui/feedback/Skeleton'
import SourceBadge from '../ui/feedback/SourceBadge'
import VerbFormTag from '../ui/text/VerbFormTag'
import BlockTitle from './BlockTitle'
import { CONJUGATIONS } from './conjugations'
import Gardaan from './Gardaan'
import InfoCard from './InfoCard'
import MeaningCard from './MeaningCard'
import TableNote from './TableNote'

/** Everything the word's answer holds: the facts, the meaning and the gardaan. */
export default function SarfResult({ data, loading, meaningPending, swapPending, swapError, onRetrySwap, accent, onForm, onGo }) {
  // A card with nothing in it is just white space, so only the facts we have
  // get a card at all. Meaning is fetched separately and can still be on its
  // way even once the rest of this list is settled, so it gets a slot of its
  // own rather than silently popping in later.
  const facts = [
    { label: 'Root (جذر)', value: data.root, arabic: true },
    { label: 'Pattern (وزن)', value: data.wazn, arabic: true },
    { label: 'Verb class', ...verbClass(data.verb_class) },
  ].filter((f) => f.value)

  return (
    <div className="space-y-4">
      {/* The table and the meaning are two different claims: the table is a rule
          applied, the meaning may be a machine's guess. Labelled separately. */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        {data.verb ? <VerbFormTag readings={data.verb.readings} /> : <span />}
        <div className="flex items-center gap-2 flex-wrap">
          <SourceBadge source={data.source} />
          {data.meaning && data.meaning_source?.key !== data.source?.key && (
            <SourceBadge source={data.meaning_source} />
          )}
        </div>
      </div>

      {/* Root first means root on the right, the way the rest of this tab reads. */}
      {(facts.length > 0 || data.meaning || meaningPending) && (
        <div dir="rtl" className="grid gap-3 grid-cols-[repeat(auto-fit,minmax(11rem,1fr))]">
          {facts.map((f, i) => (
            <InfoCard key={f.label} {...f} accent={accent} i={i} />
          ))}
          <MeaningCard
            meaning={data.meaning}
            pending={meaningPending}
            root={data.root}
            onGo={onGo}
            accent={accent}
            i={facts.length}
          />
        </div>
      )}

      {loading && !data.table && (
        <div className="space-y-2">
          <BlockTitle {...CONJUGATIONS} />
          <Skeleton className="h-48 w-full" />
        </div>
      )}

      {!data.table && data.table_note && <TableNote accent={accent}>{data.table_note}</TableNote>}
      {/* Gardaan draws the form picker with no grid when table is null, so a
          word with no recorded باب still lets the reader pick one. */}
      {(data.table || Object.keys(data.form_options ?? {}).length > 0) && (
        <Gardaan
          table={data.table}
          accent={accent}
          form={data.form}
          options={data.form_options}
          onForm={onForm}
          swapPending={swapPending}
          swapError={swapError}
          onRetrySwap={onRetrySwap}
        />
      )}

      {data.notes && (
        <TableNote accent={accent} title="Notes">{data.notes}</TableNote>
      )}
    </div>
  )
}
