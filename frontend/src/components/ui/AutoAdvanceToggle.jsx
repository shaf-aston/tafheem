import FlagButton from './FlagButton'

/**
 * The auto-advance switch. On screen all the time, under the round-wide
 * controls, because it governs the whole round rather than the answer in front
 * of you, and a setting you can only reach for one second after a right answer
 * is a setting you cannot change.
 *
 * Shared by the Quiz and Tamreen, so the same switch means the same thing in
 * both; `say` is the Urdu translator where a tab has one, and plain English
 * where it does not.
 */
export default function AutoAdvanceToggle({ value, onChange, accent, say = (s) => s }) {
  return (
    <FlagButton
      value={value}
      onChange={onChange}
      accent={accent}
      title={say('Move on by itself after an answer (A)')}
    >
      {say('auto-advance')}
      {/* A bare letter beside a word reads as a typo. Drawn as a key, the way
          the four answers draw their numbers, so it is plainly the key to press.
          Quieter by size (type-micro), not opacity, so contrast stays readable. */}
      <kbd className="type-micro rounded border border-[var(--border-hi)] px-1 text-[var(--text-dim)]">A</kbd>
    </FlagButton>
  )
}
