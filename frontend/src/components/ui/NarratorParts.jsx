/**
 * The pieces a narrator is drawn from, shared by his pop-up (NarratorSheet) and
 * his page (NarratorPage): the name, the grade pill, the facts under them, and
 * a tappable list of other narrators.
 */
import HADITH from '../../hadith.json'
import { toneOf } from '../../lib/rijal'

import { errorStatus } from '../../lib/apiError'

import ArabicText from './ArabicText'
import ErrorAlert from './ErrorAlert'
import SourceBadge from './SourceBadge'
import StatusNote from './StatusNote'

const { site: SITE, generations: GENERATIONS } = HADITH.narrator

const count = (n, noun) => `${n} ${noun}${n === 1 ? '' : 's'}`

/** How sunnah.com grades him, in the colour of his rank. */
export function GradePill({ rank, children, size = 'sm' }) {
  const tone = toneOf(rank)
  return (
    <ArabicText
      size={size}
      className="inline-block px-2 py-1 rounded-full border"
      style={{ color: `var(--${tone})`, borderColor: `var(--${tone}-edge)`, background: `var(--${tone}-wash)` }}
    >
      {children}
    </ArabicText>
  )
}

export function NarratorName({ who, as = 'h2' }) {
  return (
    <div className="min-w-0">
      <ArabicText as={as} size="lg" className="block m-0">{who.name_ar}</ArabicText>
      {who.name_en && <p className="type-small text-[var(--text-dim)] mt-1">{who.name_en}</p>}
      {who.kunya_ar && <ArabicText as="p" size="sm" className="block text-left text-[var(--text-dim)] m-0 mt-1">{who.kunya_ar}</ArabicText>}
    </div>
  )
}

/** His generation as one lit dot among Ibn Hajar's twelve, first on the right. */
function GenerationDots({ name }) {
  const at = GENERATIONS.indexOf(name)
  if (at < 0) return null
  return (
    <div dir="rtl" role="img" aria-label={`Generation ${at + 1} of ${GENERATIONS.length}`} className="flex justify-end gap-1">
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

/** Generation, years and city, each its own piece so Arabic never reorders the years; `also` adds plain pieces after. */
export function NarratorWhen({ who, also = [] }) {
  const pieces = [[who.generation_ar, true], [who.years], [who.city_ar, true], ...also.map((t) => [t])].filter(([text]) => text)
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

export function NarratorFacts({ who }) {
  const facts = [
    count(who.teachers.length, 'teacher'),
    count(who.students.length, 'student'),
    who.hadith_total != null && `${who.hadith_total} hadith`,
  ].filter(Boolean)

  return (
    <>
      {who.grade_ar && <div><GradePill rank={who.grade_rank}>{who.grade_ar}</GradePill></div>}
      <GenerationDots name={who.generation_ar} />
      <NarratorWhen who={who} />
      <p className="type-small text-[var(--text-dim)]">{facts.join(' · ')}</p>
      <div className="flex flex-wrap items-center gap-3">
        <SourceBadge source={who.source} />
        <a href={`${SITE}${who.id}`} target="_blank" rel="noreferrer" className="type-small text-[var(--text-dim)] hover:text-[var(--text)] underline underline-offset-2">
          Read on sunnah.com &#8599;
        </a>
      </div>
    </>
  )
}

/** His page's header card: name, facts and lineage held together at a reading width, so the Arabic and English sides sit close. */
export function NarratorHead({ who }) {
  return (
    <div className="mx-auto max-w-3xl space-y-3 px-6 py-5 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)]">
      <NarratorName who={who} as="h2" />
      <NarratorFacts who={who} />
      {who.lineage_ar && <ArabicText as="p" size="sm" className="block text-[var(--text-dim)] m-0">{who.lineage_ar}</ArabicText>}
    </div>
  )
}

/** A narrator that failed to load: a 404 means no page for him is built here. */
export function NarratorError({ error, onRetry }) {
  return errorStatus(error) === 404
    ? <StatusNote>No page for this narrator is built on this machine.</StatusNote>
    : <ErrorAlert title="Could not load the narrator" error={error} fallback="Try again." onRetry={onRetry} />
}

/** Narrators as tappable cards: Arabic name, grade colour, English name. `row` packs them in a wrapping line. */
export function NarratorLinks({ items, onOpen, row = false }) {
  return (
    <ul className={`list-none m-0 p-0 ${row ? 'flex flex-wrap gap-1.5' : 'grid gap-1.5 sm:grid-cols-2'}`}>
      {items.map((n) => (
        <li key={n.id} className="min-w-0">
          <button
            type="button"
            onClick={() => onOpen(n.id)}
            title={n.grade_ar || undefined}
            className="press tap w-full text-left flex items-center gap-2 px-3 py-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] hover:border-[var(--text-faint)] transition-colors"
          >
            <span
              aria-hidden="true"
              className="w-2 h-2 rounded-full shrink-0"
              style={{ background: n.grade_ar ? `var(--${toneOf(n.grade_rank)})` : 'var(--border)' }}
            />
            <span className="min-w-0">
              <ArabicText size="sm" className="block text-[var(--text)]">{n.name_ar}</ArabicText>
              {n.grade_ar && <span className="sr-only">{n.grade_ar}</span>}
              {n.name_en && !row && <span className="block type-small text-[var(--text-faint)] truncate">{n.name_en}</span>}
            </span>
          </button>
        </li>
      ))}
    </ul>
  )
}
