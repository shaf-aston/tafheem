/**
 * The pieces a narrator is drawn from, shared by his pop-up (NarratorSheet) and
 * his page (NarratorPage): the name, the grade pill, the facts under them, and
 * a tappable list of other narrators.
 */
import HADITH from '../../hadith.json'
import { toneOf } from '../../lib/rijal'

import { errorStatus } from '../../lib/apiError'

import ArabicText from '../ui/ArabicText'
import ErrorAlert from '../ui/ErrorAlert'
import SourceBadge from '../ui/SourceBadge'
import StatusNote from '../ui/StatusNote'

const { site: SITE, generations: GENERATIONS, tones: TONES } = HADITH.narrator

const count = (n, noun) => `${n} ${noun}${n === 1 ? '' : 's'}`

/** How sunnah.com grades him, in the colour of his rank. */
export function GradePill({ rank, children, size = 'sm' }) {
  const tone = toneOf(rank)
  return (
    <ArabicText
      size={size}
      className="inline-block px-2 py-1 rounded-full border"
      style={tone
        ? { color: `var(--${tone})`, borderColor: `var(--${tone}-edge)`, background: `var(--${tone}-wash)` }
        : { color: 'var(--text-dim)', borderColor: 'var(--border)' }}
    >
      {children}
    </ArabicText>
  )
}

/** One of the page's warnings beside the grade (Ikhtilat, Tadlis): the amber of a doubtful rank, so a green grade is not read as clean. */
function Flag({ arabic = false, children }) {
  const box = 'inline-block px-2 py-0.5 rounded-full border'
  const style = { color: 'var(--warn)', borderColor: 'var(--warn-edge)', background: 'var(--warn-wash)' }
  return arabic ? <ArabicText size="sm" className={box} style={style}>{children}</ArabicText> : <span className={`type-small ${box}`} style={style}>{children}</span>
}

export function NarratorName({ who, as = 'h2' }) {
  return (
    <div className="min-w-0">
      <ArabicText as={as} size="lg" className="block m-0">{who.name_ar}</ArabicText>
      {who.name_en && <p className="type-small text-[var(--text-dim)] mt-1">{who.name_en}</p>}
      {who.kunya_ar && <ArabicText as="p" size="sm" className="block text-right text-[var(--text-dim)] m-0 mt-1">{who.kunya_ar}</ArabicText>}
    </div>
  )
}

/** "Generation 4 of 12" for his generation's Arabic name, "" for one not among the twelve. */
const generationLabel = (name) => {
  const at = GENERATIONS.indexOf(name)
  return at < 0 ? '' : `Generation ${at + 1} of ${GENERATIONS.length}`
}

/** His generation as one lit dot among Ibn Hajar's twelve, first on the right. */
function GenerationDots({ name }) {
  const at = GENERATIONS.indexOf(name)
  if (at < 0) return null
  return (
    <div dir="rtl" role="img" aria-label={generationLabel(name)} className="flex gap-1">
      {GENERATIONS.map((g, i) => (
        <span
          key={g}
          title={g}
          className="w-2 h-2 rounded-full"
          style={{ background: i === at ? 'var(--text)' : i < at ? 'var(--text-faint)' : 'var(--border)' }}
        />
      ))}
    </div>
  )
}

/** Generation, years and city, each its own piece so Arabic never reorders the years; `also` adds plain pieces after, `generation={false}` leaves the generation to NarratorTerms. */
export function NarratorWhen({ who, also = [], generation = true }) {
  const pieces = [[generation && who.generation_ar, true], [who.years], [who.city_ar, true], ...also.map((t) => [t])].filter(([text]) => text)
  if (!pieces.length) return null
  return (
    <span className="type-small text-[var(--text-dim)] flex flex-wrap items-baseline gap-x-2">
      {pieces.map(([text, arabic], i) => (
        <span key={i} className="flex items-baseline gap-x-2">
          {i > 0 && <span aria-hidden="true">·</span>}
          {arabic ? <ArabicText size="sm">{text}</ArabicText> : text}
        </span>
      ))}
    </span>
  )
}

/**
 * The two terms he is placed by, his grade and his generation, each Arabic with its English beside it
 * and set as the guide sets a term (hadith/TermGuide): Arabic first, then the English in the text colour.
 */
function NarratorTerms({ who }) {
  const generation = generationLabel(who.generation_ar)
  if (!who.grade_ar && !generation) return null
  const english = 'm-0 type-ui font-medium text-[var(--text)]'
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 items-baseline m-0">
      {who.grade_ar && (
        <>
          <dt><GradePill rank={who.grade_rank}>{who.grade_ar}</GradePill></dt>
          <dd className={english}>{who.grade_en}</dd>
        </>
      )}
      {generation && (
        <>
          <dt><ArabicText size="sm" className="whitespace-nowrap">{who.generation_ar}</ArabicText></dt>
          <dd className={english}>
            {generation}
            <span className="block mt-1.5"><GenerationDots name={who.generation_ar} /></span>
          </dd>
        </>
      )}
    </dl>
  )
}

export function NarratorFacts({ who }) {
  if (who.fetched === false) return <><StatusNote>{UNFETCHED}</StatusNote><SourceLine who={who} /></>
  const facts = [
    count(who.teachers.length, 'teacher'),
    count(who.students.length, 'student'),
    who.hadith_total != null && `${who.hadith_total} hadith on sunnah.com`,
  ].filter(Boolean)

  return (
    <>
      <div className={PAIR}>
        <NarratorTerms who={who} />
        <div className="space-y-3">
          <NarratorWhen who={who} generation={false} />
          <p className="type-small text-[var(--text-dim)]">{facts.join(' · ')}</p>
        </div>
      </div>
      <SourceLine who={who} />
    </>
  )
}

/** Where his page comes from, and the link to it on sunnah.com. */
function SourceLine({ who }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <SourceBadge source={who.source} />
      <a href={`${SITE}${who.id}`} target="_blank" rel="noreferrer" className="type-small text-[var(--text-dim)] hover:text-[var(--text)] underline underline-offset-2">
        Read on sunnah.com &#8599;
      </a>
    </div>
  )
}

/** A small faint label over its value; `arabic` sets both right to left. */
function Labelled({ label, arabic = false, children }) {
  const faint = 'block text-[var(--text-faint)] mb-1'
  return arabic ? (
    <div dir="rtl" className="min-w-0">
      <ArabicText size="sm" className={faint}>{label}</ArabicText>
      <ArabicText size="base" className="block">{children}</ArabicText>
    </div>
  ) : (
    <div className="min-w-0">
      <span className={`type-tiny ${faint}`}>{label}</span>
      <span className="block type-ui">{children}</span>
    </div>
  )
}

/** Two sides of one row, English left and Arabic right as sunnah.com sets them; stacked on a phone. */
const PAIR = 'grid gap-x-10 gap-y-2 sm:grid-cols-2'

/** Said in place of the facts for a narrator known only by name from other narrators' lists. */
const UNFETCHED = 'Known here only by name, from the teacher and student lists of other narrators. His own sunnah.com page has not been fetched, so his grade, generation and counts are not shown.'


/**
 * His page's header card: the name in both languages up top as one row like the facts, then each fact
 * sunnah.com prints in both languages as one row, English left and Arabic
 * right, then the numbers, which read the same in either.
 */
export function NarratorHead({ who }) {
  const numbers = [
    // sunnah.com's years pill: a death date (d. 57 AH) or a lifespan (58 – 145 AH).
    ['Years', who.years && <>{who.years}{who.years_ar && <ArabicText size="sm" className="ms-2 text-[var(--text-dim)]">{who.years_ar}</ArabicText>}</>],
    // sunnah.com's own count; the hadith listed below are the ones this app holds, which can differ.
    ['Hadith on sunnah.com', who.hadith_total],
    ['Teachers', who.teachers.length],
    ['Students', who.students.length],
  ].filter(([, n]) => n != null && n !== '' && who.fetched !== false)
  return (
    <div className="mx-auto max-w-3xl px-6 py-5 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] divide-y divide-[var(--border)] [&>*]:py-4 [&>*:first-child]:pt-0 [&>*:last-child]:pb-0">
      <div className={`${PAIR} items-end`}>
        <div className="space-y-2 sm:order-none order-last">
          <p className="type-ui font-medium m-0">{who.name_en}</p>
          {who.alt_en && <p className="type-small text-[var(--text-dim)] m-0">{who.alt_en}</p>}
          {who.flags.some((f) => f.en) && <div className="flex flex-wrap gap-2">{who.flags.filter((f) => f.en).map((f, i) => <Flag key={i}>{f.en}</Flag>)}</div>}
        </div>
        <div className="flex flex-col items-end gap-2 text-right">
          <ArabicText as="h2" size="lg" className="block m-0">{who.name_ar}</ArabicText>
          {who.alt_ar && <ArabicText as="p" size="sm" className="block m-0 text-[var(--text-dim)]">{who.alt_ar}</ArabicText>}
          <div className="flex flex-wrap items-center justify-end gap-3">
            <GenerationDots name={who.generation_ar} />
            {who.grade_ar && <GradePill rank={who.grade_rank}>{who.grade_ar}</GradePill>}
            {who.flags.filter((f) => f.ar).map((f, i) => <Flag key={i} arabic>{f.ar}</Flag>)}
          </div>
        </div>
      </div>
      {who.fetched === false && <StatusNote>{UNFETCHED}</StatusNote>}
      {who.facts.length > 0 && (
        <div className="space-y-5">
          {who.facts.map((f, i) => (
            <div key={i} className={PAIR}>
              <Labelled label={f.label_en}>{f.en}</Labelled>
              <Labelled label={f.label_ar} arabic>{f.ar}</Labelled>
            </div>
          ))}
        </div>
      )}
      {who.books.length > 0 && (
        <div className={PAIR}>
          <div className="flex flex-wrap gap-2">{who.books.map((b, i) => <BookMark key={i}>{b.en}</BookMark>)}</div>
          <div dir="rtl" className="flex flex-wrap gap-2">{who.books.map((b, i) => <BookMark key={i} arabic>{b.ar}</BookMark>)}</div>
        </div>
      )}
      {numbers.length > 0 && (
        <dl className="m-0 grid gap-3 grid-cols-2 sm:grid-cols-4">
          {numbers.map(([label, n]) => (
            <div key={label} className="min-w-0">
              <dt className="type-tiny text-[var(--text-faint)] mb-1">{label}</dt>
              <dd className="m-0 type-ui tabular-nums">{n}</dd>
            </div>
          ))}
        </dl>
      )}
      <SourceLine who={who} />
    </div>
  )
}

/** A book that carries his hadith: a filled tag with no outline, so it does not read as a button. */
function BookMark({ arabic = false, children }) {
  const box = 'inline-block px-2.5 py-0.5 rounded-[var(--radius-sm)] bg-[var(--surface-hi)] text-[var(--text-dim)]'
  return arabic ? <ArabicText size="sm" className={box}>{children}</ArabicText> : <span className={`type-small ${box}`}>{children}</span>
}

/**
 * What the dot beside a teacher or student means, read off the same tone table
 * the dots are drawn from (hadith.json narrator.tones), so the key cannot drift
 * from the colours. Ranks are sunnah.com's, 1 the most trusted.
 */
export function GradeKey() {
  let from = 1
  const bands = Object.entries(TONES).map(([tone, top]) => {
    const band = [tone, from === top ? `rank ${top}` : `ranks ${from}–${top}`]
    from = top + 1
    return band
  })
  bands.push(['danger', `rank ${from} and below`])
  const dot = (colour) => <span aria-hidden="true" className="inline-block w-2 h-2 rounded-full me-1.5" style={{ background: colour }} />
  return (
    <p className="m-0 type-small text-[var(--text-faint)] flex flex-wrap gap-x-4 gap-y-1">
      <span>Dot: sunnah.com grade, 1 most trusted:</span>
      {bands.map(([tone, label]) => <span key={tone}>{dot(`var(--${tone})`)}{label}</span>)}
      <span>{dot('var(--text-faint)')}graded, no rank</span>
      <span>{dot('var(--border)')}no grade here</span>
    </p>
  )
}

/** A narrator that failed to load: a 404 means no page for him is built here. */
export function NarratorError({ error, onRetry }) {
  return errorStatus(error) === 404
    ? <StatusNote>No page for this narrator is built on this machine.</StatusNote>
    : <ErrorAlert title="Could not load the narrator" error={error} fallback="Try again." onRetry={onRetry} />
}

/**
 * One tappable row set as sunnah.com lists a narrator's people and hadith: the
 * Arabic on the right, with an optional dot after it, and the English on the left.
 */
export function PairRow({ en, ar, dot, title, hint, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      className="press tap w-full flex items-center gap-3 py-2 hover:bg-[var(--surface)] transition-colors"
    >
      {en && <span className="min-w-0 shrink-0 max-w-[45%] text-left type-small text-[var(--text-dim)] truncate">{en}</span>}
      <span className="min-w-0 flex-1 flex items-center justify-end gap-2">
        <ArabicText size="sm" className="min-w-0 truncate text-[var(--text)]">{ar}</ArabicText>
        {dot && <span aria-hidden="true" className="w-2 h-2 rounded-full shrink-0" style={{ background: dot }} />}
      </span>
      {hint && <span className="sr-only">{hint}</span>}
    </button>
  )
}

/** Rows divided by a hairline, the list PairRow sits in. */
export const PAIR_ROWS = 'list-none m-0 p-0 divide-y divide-[var(--border)]'

/** Narrators as tappable rows (PairRow). `row` packs Arabic-only pills in a wrapping line instead. */
export function NarratorLinks({ items, onOpen, row = false }) {
  const dot = (n) => { const tone = n.grade_ar && toneOf(n.grade_rank); return tone ? `var(--${tone})` : n.grade_ar ? 'var(--text-faint)' : 'var(--border)' }
  return (
    <ul className={row ? 'list-none m-0 p-0 flex flex-wrap gap-1.5' : PAIR_ROWS}>
      {items.map((n) => (
        <li key={n.id} className="min-w-0">
          {row ? (
            <button
              type="button"
              onClick={() => onOpen(n.id)}
              title={n.grade_ar || undefined}
              className="press tap flex items-center gap-2 px-3 py-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] hover:border-[var(--text-faint)] transition-colors"
            >
              <span aria-hidden="true" className="w-2 h-2 rounded-full shrink-0" style={{ background: dot(n) }} />
              <ArabicText size="sm" className="text-[var(--text)]">{n.name_ar}</ArabicText>
              {n.grade_ar && <span className="sr-only">{n.grade_ar}</span>}
            </button>
          ) : (
            <PairRow en={n.name_en} ar={n.name_ar} dot={dot(n)} title={n.grade_ar || undefined} hint={n.grade_ar} onClick={() => onOpen(n.id)} />
          )}
        </li>
      ))}
    </ul>
  )
}
