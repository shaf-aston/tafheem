/**
 * One narrator on his own page: who he was, what scholars said of him, who he
 * learnt from and taught (each a tap to that narrator's page), and the hadith
 * he narrates in the books built here, each a tap into the reader.
 *
 * A 404 means this machine holds no page for him (rijal.db unbuilt, or he was
 * never fetched), said in a line, as on his pop-up.
 */
import { useQuery } from '@tanstack/react-query'

import { narratorHadithQuery, narratorQuery } from '../api'
import { errorStatus } from '../lib/apiError'
import { useHadithCollections } from '../lib/useHadithCollections'

import ArabicText from './ui/ArabicText'
import Chip from './ui/Chip'
import ChipRow from './ui/ChipRow'
import ErrorAlert from './ui/ErrorAlert'
import { NarratorFacts, NarratorLinks, NarratorName } from './ui/NarratorParts'
import ShowRest from './ui/ShowRest'
import { AnalyzerSkeleton } from './ui/Skeleton'
import StatusNote from './ui/StatusNote'

const Section = ({ title, children }) => (
  <section className="space-y-2">
    <h3 className="type-ui font-medium text-[var(--text)]">{title}</h3>
    {children}
  </section>
)

export default function NarratorPage({ id, accent, onBack, onNarrator, onHadith }) {
  const { data: who, isPending, isError, error, refetch } = useQuery(narratorQuery(id))
  const { data: hadith = [] } = useQuery(narratorHadithQuery(id))
  const { of } = useHadithCollections()

  return (
    <div className="space-y-4 max-w-3xl">
      <button type="button" onClick={onBack} className="press type-small text-[var(--text-faint)] hover:text-[var(--text)] transition-colors">
        &larr; Back
      </button>

      {isPending && <AnalyzerSkeleton />}
      {isError && (errorStatus(error) === 404
        ? <StatusNote>No page for this narrator is built on this machine.</StatusNote>
        : <ErrorAlert title="Could not load the narrator" error={error} fallback="Try again." onRetry={refetch} />)}

      {who && (
        <>
          <div className="space-y-3">
            <NarratorName who={who} as="h2" />
            <NarratorFacts who={who} />
            {who.lineage_ar && <ArabicText as="p" size="sm" className="block text-[var(--text-dim)] m-0">{who.lineage_ar}</ArabicText>}
          </div>

          {who.verdicts.length > 0 && (
            <Section title="What scholars said">
              <ShowRest lines={6} accent={accent}>
                <ul className="list-none m-0 p-0 space-y-3">
                  {who.verdicts.map((v, i) => (
                    <li key={i}>
                      <ArabicText as="p" size="sm" className="block m-0 text-[var(--text)]">{v.scholar}</ArabicText>
                      <ArabicText as="p" size="sm" className="block m-0 text-[var(--text-dim)]">{v.quote}</ArabicText>
                    </li>
                  ))}
                </ul>
              </ShowRest>
            </Section>
          )}

          {[['Teachers', who.teachers], ['Students', who.students]].map(([title, list]) => list.length > 0 && (
            <Section key={title} title={`${title} (${list.length})`}>
              <ShowRest lines={12} accent={accent} more={`Show all ${list.length}`}>
                <NarratorLinks items={list} onOpen={onNarrator} />
              </ShowRest>
            </Section>
          ))}

          {hadith.length > 0 && (
            <Section title="Hadith he narrates in the books built here">
              <ChipRow>
                {hadith.map((h) => (
                  <Chip key={`${h.collection}:${h.number}${h.part}`} accent={accent} onClick={() => onHadith(h)}>
                    {of(h.collection).short} {h.number}{h.part}
                  </Chip>
                ))}
              </ChipRow>
            </Section>
          )}
        </>
      )}
    </div>
  )
}
