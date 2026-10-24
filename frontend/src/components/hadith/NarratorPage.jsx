/**
 * One narrator on his own page: who he was, what scholars said of him, who he
 * learnt from and taught (each a tap to that narrator's page), and the hadith
 * he narrates in the six books, each a tap into the reader. Under his header, what the
 * narrator books say of him in four groups (hadith/BookFacts).
 *
 * A 404 means this machine holds no page for him (rijal.db unbuilt, or he was
 * never fetched), said in a line, as on his pop-up.
 */
import { useQuery } from '@tanstack/react-query'

import { narratorHadithQuery, narratorQuery } from '../../api'
import { useOpenAtTop } from '../../lib/motion/scrollToEl'

import ArabicText from '../ui/ArabicText'
import Disclosure from '../ui/Disclosure'
import BookFacts from './BookFacts'
import ClassicalText from './ClassicalText'
import NarratorHadith from './NarratorHadith'
import { FoldedList, GradeKey, NarratorError, NarratorHead, NarratorLinks } from './NarratorParts'
import ErrorAlert from '../ui/ErrorAlert'
import ShowRest from '../ui/ShowRest'
import { AnalyzerSkeleton } from '../ui/Skeleton'

/** A section headed in both languages, English left and Arabic right, as the header card sets its facts. */
const Section = ({ title, ar, children }) => (
  <section className="flex flex-col gap-3">
    <h3 className="m-0 flex items-baseline justify-between gap-4 pb-2 border-b border-[var(--border)]">
      <span className="type-body font-semibold text-[var(--text)]">{title}</span>
      {ar && <ArabicText size="base" className="text-[var(--text)]">{ar}</ArabicText>}
    </h3>
    {children}
  </section>
)

export default function NarratorPage({ id, accent, onNarrator, onHadith }) {
  useOpenAtTop(id)
  const { data: who, isPending, isError, error, refetch } = useQuery(narratorQuery(id))
  const { data: hadith = [], isPending: hadithLoading, isError: hadithFailed, error: hadithError, refetch: refetchHadith } = useQuery(narratorHadithQuery(id))

  return (
    <div className="space-y-10">
      {isPending && <AnalyzerSkeleton />}
      {isError && <NarratorError error={error} onRetry={refetch} />}

      {who && (
        <>
          <NarratorHead who={who} />

          <BookFacts usul={who.usul} accent={accent} />

          {who.verdicts.length > 0 && (
            <Section title="What scholars said" ar="الجرح والتعديل">
              {/* Two to a row where there is room: one short quote a row left most of a wide screen empty. */}
              <FoldedList key={`${id}:verdicts`} items={who.verdicts} accent={accent}>
                {(shown) => (
                  <ul dir="rtl" className="list-none m-0 p-0 mb-2 grid gap-2 md:grid-cols-2">
                    {shown.map((v, i) => (
                      <li key={i} className="px-4 py-3 rounded-[var(--radius-md)] rounded-s-none bg-[var(--surface)] border-s-2" style={{ borderColor: accent }}>
                        <ArabicText as="p" size="sm" className="block m-0 font-medium" style={{ color: accent }}>{v.scholar}</ArabicText>
                        <ArabicText as="p" size="sm" className="block m-0 text-[var(--text-dim)]">{v.quote}</ArabicText>
                      </li>
                    ))}
                  </ul>
                )}
              </FoldedList>
            </Section>
          )}

          {/* Teachers and students side by side where the width allows, one column on a phone. */}
          {/* The grade key sits with the lists its dots are on, not as a section of its own. */}
          {(who.teachers.length > 0 || who.students.length > 0) && (
            <div className="space-y-3">
              <div className="grid gap-x-8 gap-y-10 grid-cols-[repeat(auto-fit,minmax(min(100%,22rem),1fr))] [&>*]:min-w-0">
                {[['Teachers', 'المشايخ', who.teachers], ['Students', 'التلاميذ', who.students]].map(([title, ar, list]) => list.length > 0 && (
                  <Section key={title} title={`${title} · ${list.length}`} ar={ar}>
                    <FoldedList key={`${id}:${title}`} items={list} accent={accent}>
                      {(shown) => <NarratorLinks items={shown} onOpen={onNarrator} />}
                    </FoldedList>
                  </Section>
                ))}
              </div>
              <GradeKey />
            </div>
          )}

          {hadithFailed && <ErrorAlert title="Could not load the hadith he narrates" error={hadithError} fallback="Try again." onRetry={refetchHadith} />}

          {hadithLoading && <p className="type-small text-[var(--text-faint)] m-0">Finding the hadith he narrates…</p>}
          {hadith.length > 0 && (
            <Section title={`Hadith narrated · ${who.hadith_count}`} ar="الأحاديث المروية">
              <NarratorHadith key={id} rows={hadith} total={who.hadith_count} accent={accent} onHadith={onHadith} />
            </Section>
          )}

          {/* Each classical book shut until asked for, as sunnah.com's rijal texts: four walls of Arabic
              one under another buried everything after the first. */}
          {who.texts.length > 0 && (
            <Section title="In the classical books" ar="كتب الرجال">
              <div className="space-y-2">
                {who.texts.map((t, i) => (
                  <Disclosure
                    key={`${id}:${i}:${t.book}`}
                    framed
                    label={<ArabicText size="sm" className="block text-left text-[var(--text)]">{t.book}</ArabicText>}
                    bodyClassName="px-4 py-3"
                  >
                    <ShowRest lines={14} accent={accent}>
                      <ClassicalText text={t} accent={accent} />
                    </ShowRest>
                  </Disclosure>
                ))}
              </div>
            </Section>
          )}
        </>
      )}
    </div>
  )
}
