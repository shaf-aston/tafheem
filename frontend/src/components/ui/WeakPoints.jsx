/**
 * Where a chain may be weak, one row for each weak narrator, weakest first
 * (lib/weak weakPoints): his rank, name and grade as the data words it, where
 * the level sits on Ibn Hajar's twelve, what it means in plain English, and the
 * book it comes from. The lift line is there only where a source speaks of
 * support lifting that weakness, and quotes it. No legend: each row carries
 * its own words.
 */
import ArabicText from './ArabicText'
import NarratorLink from './NarratorLink'
import ShowRest from './ShowRest'

/** The twelve levels as steps: the narrator's filled, the levels too strong to be a weak point muted. */
function Scale({ level, scale }) {
  return (
    <div role="img" aria-label={`level ${level} of ${scale.length}`} dir="ltr" className="flex gap-0.5">
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

export default function WeakPoints({ points, scale, onNarrator }) {
  if (!points.length) return null
  return (
    <section aria-labelledby="weak-points" className="mt-4 pt-4 border-t border-[var(--border)]">
      <h3 id="weak-points" className="type-small font-semibold text-[var(--text-dim)] mb-3">Weak points</h3>
      <ol className="list-none m-0 p-0 space-y-4">
        {points.map((p) => (
          <li key={p.at} className="flex gap-3">
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
                  <ShowRest lines={2} more="Show the rest" less="Show less">
                    <ArabicText as="p" size="sm" className="block m-0 leading-loose text-[var(--text-faint)]">{p.lift.quote}</ArabicText>
                  </ShowRest>
                  <p className="type-tiny m-0 text-[var(--text-faint)]">{p.lift.source}</p>
                </div>
              )}
              <p className="type-tiny m-0 text-[var(--text-faint)]">{p.source}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  )
}
