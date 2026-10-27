/**
 * The number on an answer, the key that picks it: the Quiz's, Colloquial's and Grow's options all wear this one.
 * It sits a shade off its button: `--option-number-bg` where the button is itself on --surface (Grow).
 */
export default function OptionNumber({ index }) {
  return (
    <span className="shrink-0 w-6 h-6 grid place-items-center rounded-full type-small bg-[var(--option-number-bg,var(--surface))] text-[var(--text-faint)]" aria-hidden="true">
      {index + 1}
    </span>
  )
}
