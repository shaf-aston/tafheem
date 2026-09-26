/**
 * The few pieces every Colloquial screen repeats, drawn once so a row, a card
 * and a line of gloss cannot drift apart between the unit list, the lesson list
 * and the lesson. Classes are the ones Tamreen and the notes already use.
 */
import SmallButton from '../components/ui/SmallButton'
import config from '../colloquial.json'

export const COPY = config.copy

/** A titled card: one lesson section. */
export function Section({ title, children }) {
  return (
    <section className="rounded-[var(--radius-md)] border border-[var(--border)] p-3 space-y-2">
      <h3 className="type-tiny uppercase tracking-wide text-[var(--text-faint)]">{title}</h3>
      {children}
    </section>
  )
}

/** Transliteration and English under an Arabic line, left to right. */
export function Gloss({ translit, en }) {
  return (
    <p dir="ltr" className="type-small text-[var(--text-dim)]">
      {translit && <i>{translit}</i>}
      {translit && en && ' · '}
      {en}
    </p>
  )
}

/** One choice in a list: a unit or a lesson. */
export function Row({ onClick, disabled, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="lift press w-full text-left rounded-[var(--radius-md)] border border-[var(--border)] p-3
        hover:border-[var(--c)] disabled:opacity-50 disabled:hover:border-[var(--border)]"
    >
      {children}
    </button>
  )
}

export function Back({ onClick }) {
  return <SmallButton onClick={onClick}>← {COPY.back}</SmallButton>
}
