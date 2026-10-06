/**
 * One narrator on his own page: who he was, what scholars said of him, who he
 * learnt from and taught (each a tap to that narrator's page), and the hadith
 * he narrates in the six books, each a tap into the reader.
 *
 * A 404 means this machine holds no page for him (rijal.db unbuilt, or he was
 * never fetched), said in a line, as on his pop-up.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { narratorHadithQuery, narratorQuery } from '../api'
import { useHadithCollections } from '../lib/useHadithCollections'

import ArabicText from './ui/ArabicText'
import Chip from './ui/Chip'
import ChipRow from './ui/ChipRow'
import { NarratorError, NarratorHead, NarratorLinks } from './ui/NarratorParts'
import ShowRest from './ui/ShowRest'
import { AnalyzerSkeleton } from './ui/Skeleton'

const Section = ({ title, children }) => (
  <section className="space-y-2">
    <h3 className="type-ui font-medium text-[var(--text)]">{title}</h3>
    {children}
  </section>
)

// Rows drawn while a list is folded. Abu Hurayra narrates thousands of hadith;
// drawing and measuring every chip behind the fold took the page over a second.
const FOLDED_ROWS = 80

// A long list folded under "Show all N", drawing the rest only once opened.
function FoldedList({ items, lines, accent, children: draw }) {
  const [open, setOpen] = useState(false)
  return (
    <ShowRest lines={lines} accent={accent} more={`Show all ${items.length}`} open={open} onOpenChange={setOpen}>
      {draw(open ? items : items.slice(0, FOLDED_ROWS))}
    </ShowRest>
  )
}

export default function NarratorPage({ id, accent, onBack, onNarrator, onHadith }) {
  const { data: who, isPending, isError, error, refetch } = useQuery(narratorQuery(id))
  const { data: hadith = [] } = useQuery(narratorHadithQuery(id))
  const { of } = useHadithCollections()

  return (
    <div className="space-y-4">
      <button type="button" onClick={onBack} className="press type-small text-[var(--text-faint)] hover:text-[var(--text)] transition-colors">
        &larr; Back
      </button>

      {isPending && <AnalyzerSkeleton />}
      {isError && <NarratorError error={error} onRetry={refetch} />}

      {who && (
        <>
          <NarratorHead who={who} />

          {/* The three side by side where the width allows, one column on a phone. */}
          <div className="grid gap-x-6 gap-y-4 grid-cols-[repeat(auto-fit,minmax(min(100%,18rem),1fr))] [&>*]:min-w-0">
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
              <FoldedList items={list} lines={12} accent={accent}>
                {(shown) => <NarratorLinks items={shown} onOpen={onNarrator} />}
              </FoldedList>
            </Section>
          ))}
          </div>

          {hadith.length > 0 && (
            <Section title={`Hadith narrated (${hadith.length})`}>
              <FoldedList items={hadith} lines={6} accent={accent}>
                {(shown) => (<ChipRow>
                  {shown.map((h) => (
                    <Chip key={`${h.collection}:${h.number}${h.part}`} accent={accent} onClick={() => onHadith(h)}>
                      {of(h.collection).short} {h.number}{h.part}
                    </Chip>
                  ))}
                </ChipRow>)}
              </FoldedList>
            </Section>
          )}

          {who.texts.map((t) => (
            <Section key={t.book} title={<ArabicText size="sm">{t.book}</ArabicText>}>
              <ShowRest lines={8} accent={accent}>
                <ArabicText as="p" size="sm" className="block m-0 whitespace-pre-line text-[var(--text-dim)]">{t.body}</ArabicText>
              </ShowRest>
            </Section>
          ))}
        </>
      )}
    </div>
  )
}
