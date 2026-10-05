/**
 * The pop-up about one narrator of a chain, tapped in a hadith. His name, how
 * sunnah.com grades him, when and where he lived, how many he taught and was
 * taught by, and a link to his page there. A 404 means this machine holds no
 * page for him (rijal.db unbuilt or he was never fetched), said in a line.
 */
import { useQuery } from '@tanstack/react-query'

import { narratorQuery } from '../../api'
import HADITH from '../../hadith.json'
import { errorStatus } from '../../lib/apiError'

import ArabicText from './ArabicText'
import BottomSheet from './BottomSheet'
import CloseButton from './CloseButton'
import ErrorAlert from './ErrorAlert'
import SourceBadge from './SourceBadge'
import { Skeleton } from './Skeleton'
import StatusNote from './StatusNote'

const { site: SITE, tones: TONES } = HADITH.narrator

// The tone a grade wears: the first whose highest rank covers it, else danger.
const toneOf = (rank) => Object.entries(TONES).find(([, top]) => rank <= top)?.[0] ?? 'danger'

const count = (n, noun) => `${n} ${noun}${n === 1 ? '' : 's'}`

export default function NarratorSheet({ id, onClose }) {
  const { data: who, isPending, isError, error, refetch } = useQuery(narratorQuery(id))
  // Arabic and the years in turn, each its own piece so the years keep their order.
  const when = who ? [[who.generation_ar, true], [who.years], [who.city_ar, true]].filter(([text]) => text) : []
  const facts = [
    count(who?.teachers.length ?? 0, 'teacher'),
    count(who?.students.length ?? 0, 'student'),
    who?.hadith_total != null && `${who.hadith_total} hadith`,
  ].filter(Boolean)

  return (
    <BottomSheet label="Narrator" onClose={onClose} className="max-h-[var(--sheet-tall)] flex flex-col">
      <header className="flex items-start justify-between gap-3 px-5 pt-4 pb-3">
        {who ? (
          <div className="min-w-0">
            <ArabicText as="h2" size="lg" className="block m-0">{who.name_ar}</ArabicText>
            {who.name_en && <p className="type-small text-[var(--text-dim)] mt-1">{who.name_en}</p>}
            {who.kunya_ar && <ArabicText as="p" size="sm" className="block text-left text-[var(--text-dim)] m-0 mt-1">{who.kunya_ar}</ArabicText>}
          </div>
        ) : <h2 className="type-ui font-semibold text-[var(--text)]">Narrator</h2>}
        <CloseButton onClick={onClose} className="shrink-0" />
      </header>

      <div className="overflow-y-auto px-5 pb-5 space-y-3">
        {isPending && <Skeleton className="h-24 w-full" />}
        {isError && (errorStatus(error) === 404
          ? <StatusNote>No page for this narrator is built on this machine.</StatusNote>
          : <ErrorAlert title="Could not load the narrator" error={error} fallback="Try again." onRetry={refetch} />)}
        {who && (
          <>
            {who.grade_ar && (
              <ArabicText
                size="sm"
                className="inline-block px-2 py-1 rounded-full border"
                style={{
                  color: `var(--${toneOf(who.grade_rank)})`,
                  borderColor: `var(--${toneOf(who.grade_rank)}-edge)`,
                  background: `var(--${toneOf(who.grade_rank)}-wash)`,
                }}
              >
                {who.grade_ar}
              </ArabicText>
            )}
            {when.length > 0 && (
              <p className="type-small text-[var(--text-dim)] flex flex-wrap items-baseline gap-x-2">
                {when.map(([text, arabic], i) => (
                  <span key={i} className="flex items-baseline gap-x-2">
                    {i > 0 && <span aria-hidden="true">·</span>}
                    {arabic ? <ArabicText size="sm">{text}</ArabicText> : text}
                  </span>
                ))}
              </p>
            )}
            <p className="type-small text-[var(--text-dim)]">{facts.join(' · ')}</p>
            <div className="flex flex-wrap items-center gap-3">
              <SourceBadge source={who.source} />
              <a href={`${SITE}${who.id}`} target="_blank" rel="noreferrer" className="type-small text-[var(--text-dim)] hover:text-[var(--text)] underline underline-offset-2">
                Read on sunnah.com &#8599;
              </a>
            </div>
          </>
        )}
      </div>
    </BottomSheet>
  )
}
