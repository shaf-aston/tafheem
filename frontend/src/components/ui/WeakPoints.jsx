/**
 * Where a chain may be weak, one row for each weak narrator, weakest first
 * (lib/weak weakPoints): his rank, name and grade as the data words it, where
 * the level sits on Ibn Hajar's twelve, what it means in plain English, and the
 * book it comes from. The lift line is there only where a source speaks of
 * support lifting that weakness; its quote waits behind the book's name. No legend: each row carries
 * its own words.
 *
 * Under them, the links of the chain a source puts in doubt, in chain order
 * from the top of the drawing, each with the letter marked on its rung (lib/weak
 * weakLinks): who said which word to whom, what the source says of it, and the
 * quotes with their book and page. Links are never ranked against narrators.
 */
import ArabicText from './ArabicText'
import Disclosure from './Disclosure'
import NarratorLink from './NarratorLink'

/** The twelve levels as steps: the narrator's filled, the levels too strong to be a weak point muted. */
function Scale({ level, scale }) {
  return (
    <div role="img" aria-label={`level ${level} of ${scale.length}, ${scale.length} is the weakest`} dir="ltr" className="flex gap-0.5">
      {scale.map((row) => (
        <span
          key={row.level}
          className={`h-1.5 w-4 rounded-sm ${row.level === level
            ? 'bg-[var(--hadith-weak)]'
            : row.weak ? 'bg-[var(--border-hi)]' : 'bg-[var(--border)] opacity-50'}`}
        />
      ))}
    </div>
  )
}

/** A doubtful link: its letter, who said the word to whom, what the sources say of it, the quotes behind their book. */
function LinkRow({ point, onNarrator }) {
  return (
    <li className="flex gap-3">
      <span className="type-ui tabular-nums w-7 shrink-0 text-[var(--hadith-weak)]">{point.letter}</span>
      <div className="min-w-0 flex-1 space-y-1.5">
        <p className="type-small m-0 text-[var(--text-dim)]">{point.label}</p>
        <ArabicText size="base" className="block leading-relaxed">
          <>
            <NarratorLink id={point.student} onOpen={onNarrator}>{point.teller}</NarratorLink>
            <span className="mx-2 text-[var(--text-dim)] underline decoration-dotted underline-offset-4 decoration-[var(--hadith-weak)]">{point.word}</span>
            <NarratorLink id={point.teacher} onOpen={onNarrator}>{point.teacherName}</NarratorLink>
          </>
        </ArabicText>
        {point.says.map((line) => <p key={line} className="type-ui m-0 text-[var(--text)]">{line}</p>)}
        {point.scholar && (
          <p className="type-small m-0 text-[var(--text-dim)]">
            Said by <ArabicText size="sm">{point.scholar}</ArabicText>
          </p>
        )}
        <div className="space-y-1">
          {point.quotes.map((q) => (
            <Disclosure key={`${q.source}${q.page}${q.quote}`} label={`Quote: ${[q.source, q.page].filter(Boolean).join(', ')}`}>
              <ArabicText as="p" size="sm" className="block m-0 leading-loose text-[var(--text-faint)]">{q.quote}</ArabicText>
            </Disclosure>
          ))}
        </div>
      </div>
    </li>
  )
}

const GROUP = 'type-small font-medium text-[var(--text)] m-0 mt-3 mb-1'

export default function WeakPoints({ points, linkPoints = [], scale, onNarrator }) {
  if (!points.length && !linkPoints.length) return null
  const both = points.length > 0 && linkPoints.length > 0
  return (
    <section aria-labelledby="weak-points" className="mt-4 pt-4 border-t border-[var(--border)]">
      <h3 id="weak-points" className="type-small font-semibold text-[var(--text-dim)] m-0">Weak points</h3>
      {points.length > 0 && (
        <>
          {both && <h4 className={GROUP}>Narrators</h4>}
          <p className="type-tiny m-0 mb-3 text-[var(--text-faint)]">1 is the weakest. Levels from {points[0].source}.</p>
          <ol className="list-none m-0 p-0 space-y-4">
            {points.map((p) => (
              <li key={p.id} className="flex gap-3">
                <span className="type-ui tabular-nums w-7 shrink-0 text-[var(--hadith-weak)]">{p.label}</span>
                <div className="min-w-0 flex-1 space-y-1.5">
                  <div className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
                    <ArabicText size="base" className="leading-relaxed">
                      <NarratorLink id={p.id} onOpen={onNarrator}>{p.name}</NarratorLink>
                    </ArabicText>
                    <ArabicText size="sm" className="text-[var(--text-dim)]">{p.grade}</ArabicText>
                  </div>
                  <Scale level={p.level} scale={scale} />
                  <p className="type-ui m-0 text-[var(--text)]">{p.en}</p>
                  {p.lift && (
                    <div className="ps-3 border-s border-[var(--border-hi)] space-y-1">
                      <p className="type-small m-0 text-[var(--text-dim)]">{p.lift.en}</p>
                      <Disclosure label={`Quote: ${p.lift.source}`}>
                        <ArabicText as="p" size="sm" className="block m-0 leading-loose text-[var(--text-faint)]">{p.lift.quote}</ArabicText>
                      </Disclosure>
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </>
      )}
      {linkPoints.length > 0 && (
        <div className={points.length ? 'mt-5' : ''}>
          {both && <h4 className={GROUP}>Links</h4>}
          <p className="type-tiny m-0 mb-3 text-[var(--text-faint)]">Links are not ranked against narrators: no source we hold orders them.</p>
          <ul className="list-none m-0 p-0 space-y-4">
            {linkPoints.map((p) => <LinkRow key={p.key} point={p} onNarrator={onNarrator} />)}
          </ul>
        </div>
      )}
    </section>
  )
}
