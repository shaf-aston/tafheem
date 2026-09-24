/**
 * The root is the same word in every tab, so it should be one click, not retyping.
 *
 * Arabic hangs almost everything off a three-letter root. A root you meet in an
 * ayah is the root the dictionary defines and the root the conjugator builds a
 * table for. These buttons carry it across, which is what stops the five tabs
 * being five separate apps.
 */
import ArabicText from './ArabicText'


// Where a root can go, and what it is called there. Adding a destination is a
// line here; no panel needs to know about the others.
const DESTINATIONS = [
  { tab: 'sarf', label: 'Conjugate', hint: 'Build the full table for this root' },
  { tab: 'dict', label: 'Define', hint: 'Look this root up in the dictionary' },
  { tab: 'quran', label: 'In the Qur’an', hint: 'Every place this root appears' },
]

// The pill styling for a root-destination button, shared so Dictionary's own
// use of the same look (if any) never drifts from this one.
export function GoButton({ children, ...props }) {
  return (
    <button
      type="button"
      className="type-small leading-none px-2 py-1 rounded-full
        border border-[var(--border)] text-[var(--text-dim)]
        hover:text-[var(--text)] hover:border-[var(--c)] transition-colors"
      {...props}
    >
      {children}
    </button>
  )
}

export default function RootActions({ root, onGo, exclude = '', className = '', showRoot = true }) {
  if (!root) return null

  return (
    <div className={`flex flex-wrap items-center gap-1 ${className}`}>
      {showRoot && (
        <ArabicText className="text-[var(--text-faint)]">
          {root}
        </ArabicText>
      )}
      {DESTINATIONS.filter((d) => d.tab !== exclude).map((d) => (
        <GoButton key={d.tab} onClick={() => onGo(d.tab, root)} title={d.hint}>
          {d.label}
        </GoButton>
      ))}
    </div>
  )
}
