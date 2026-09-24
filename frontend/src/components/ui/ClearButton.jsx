/** Empties an input from inside it. Present whenever there is something to clear. */
export default function ClearButton({ onClick, label, className = '' }) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={onClick}
      className={`absolute text-[var(--text-faint)] hover:text-[var(--text)] transition-colors
        text-sm leading-none w-6 h-6 grid place-items-center rounded-full
        hover:bg-[var(--surface-hi)] ${className}`}
    >
      ✕
    </button>
  )
}
