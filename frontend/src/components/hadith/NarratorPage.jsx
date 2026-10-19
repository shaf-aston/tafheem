/**
 * One narrator on his own page: who he was, what scholars said of him, who he
 * learnt from and taught (each a tap to that narrator's page), and the hadith
 * he narrates in the six books, each a tap into the reader. Under his header, what the
 * narrator books say of him in four groups (hadith/BookFacts).
 *
 * A 404 means this machine holds no page for him (rijal.db unbuilt, or he was
 * never fetched), said in a line, as on his pop-up.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { narratorHadithQuery, narratorQuery } from '../../api'
import { useHadithCollections } from '../../lib/useHadithCollections'
import { useOpenAtTop } from '../../lib/scrollToEl'

import ArabicText from '../ui/ArabicText'
import BookFacts from './BookFacts'
import ClassicalText from './ClassicalText'
import { GradeKey, NarratorError, NarratorHead, NarratorLinks, PAIR_ROWS, PairRow } from './NarratorParts'
import ErrorAlert from '../ui/ErrorAlert'
import ShowRest from '../ui/ShowRest'
import { AnalyzerSkeleton } from '../ui/Skeleton'

/** A section headed in both languages, English left and Arabic right, as the header card sets its facts. */
const Section = ({ title, ar, children }) => (
  <section className="space-y-3">
    <h3 className="m-0 flex items-baseline justify-between gap-4 pb-2 border-b border-[var(--border)]">
      <span className="type-ui font-medium text-[var(--text)]">{title}</span>
      {ar && <ArabicText size="base" className="text-[var(--text)]">{ar}</ArabicText>}
    </h3>
    {children}
  </section>
)

// Rows drawn while a list is folded. Abu Hurayra narrates thousands of hadith;
// drawing and measuring every chip behind the fold took the page over a second.
const FOLDED_ROWS = 80

// A long list folded under "Show all N", drawing the rest only once opened.
function FoldedList({ items, lines, accent, total = items.length, children: draw }) {
  const [open, setOpen] = useState(false)
  return (
    <ShowRest lines={lines} accent={accent} more={`Show all ${items.length}`} open={open} onOpenChange={setOpen}>
      {draw(open ? items : items.slice(0, FOLDED_ROWS))}
      {open && total > items.length && <p className="type-small text-[var(--text-faint)] mt-2 mb-0">Showing the first {items.length} of {total}.</p>}
    </ShowRest>
  )
}

export default function NarratorPage({ id, accent, onNarrator, onHadith }) {
  useOpenAtTop(id)
  const { data: who, isPending, isError, error, refetch } = useQuery(narratorQuery(id))
  const { data: hadith = [], isError: hadithFailed, error: hadithError, refetch: refetchHadith } = useQuery(narratorHadithQuery(id))
  const { of } = useHadithCollections()

  return (
    <div className="space-y-4">
      {isPending && <AnalyzerSkeleton />}
      {isError && <NarratorError error={error} onRetry={refetch} />}

      {who && (
        <>
          <NarratorHead who={who} />

          <BookFacts usul={who.usul} accent={accent} />

          {who.verdicts.length > 0 && (
            <Section title="What scholars said" ar="الجرح والتعديل">
              <ShowRest lines={9} accent={accent}>
                <ul dir="rtl" className="list-none m-0 p-0 space-y-2">
                  {who.verdicts.map((v, i) => (
                    <li key={i} className="px-4 py-3 rounded-[var(--radius-md)] rounded-s-none bg-[var(--surface)] border-s-2" style={{ borderColor: accent }}>
                      <ArabicText as="p" size="sm" className="block m-0 font-medium" style={{ color: accent }}>{v.scholar}</ArabicText>
                      <ArabicText as="p" size="sm" className="block m-0 text-[var(--text-dim)]">{v.quote}</ArabicText>
                    </li>
                  ))}
                </ul>
              </ShowRest>
            </Section>
          )}

          {/* Teachers and students side by side where the width allows, one column on a phone. */}
          <div className="grid gap-x-8 gap-y-6 grid-cols-[repeat(auto-fit,minmax(min(100%,22rem),1fr))] [&>*]:min-w-0">
            {[['Teachers', 'المشايخ', who.teachers], ['Students', 'التلاميذ', who.students]].map(([title, ar, list]) => list.length > 0 && (
              <Section key={title} title={title} ar={ar}>
                <FoldedList key={`${id}:${title}`} items={list} lines={10} accent={accent}>
                  {(shown) => <NarratorLinks items={shown} onOpen={onNarrator} />}
                </FoldedList>
              </Section>
            ))}
          </div>
          {(who.teachers.length > 0 || who.students.length > 0) && <GradeKey />}

          {hadithFailed && <ErrorAlert title="Could not load the hadith he narrates" error={hadithError} fallback="Try again." onRetry={refetchHadith} />}

          {hadith.length > 0 && (
            <Section title="Hadith narrated" ar="الأحاديث المروية">
              <FoldedList key={id} items={hadith} total={who.hadith_count} lines={10} accent={accent}>
                {(shown) => (<ul className={PAIR_ROWS}>
                  {shown.map((h) => (
                    <li key={`${h.collection}:${h.number}${h.part}`} className="min-w-0">
                      <PairRow en={`${of(h.collection).short} ${h.number}${h.part}`} ar={h.opening} onClick={() => onHadith(h)} />
                    </li>
                  ))}
                </ul>)}
              </FoldedList>
            </Section>
          )}

          {who.texts.map((t, i) => (
            <Section key={`${i}:${t.book}`} ar={t.book}>
              <ShowRest lines={8} accent={accent}>
                <ClassicalText text={t} accent={accent} />
              </ShowRest>
            </Section>
          ))}
        </>
      )}
    </div>
  )
}
