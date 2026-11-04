/**
 * A standing on/off preference, drawn as a quiet pill with a dot that fills
 * when on. Quieter than everything around it on purpose: it is a setting, not
 * something to read each time. auto-advance and Lane's tidy view both use it,
 * so a switch looks the same wherever one appears.
 */
export default function FlagButton({ value, onChange, accent, title, children }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!value)}
      aria-pressed={value}
      title={title}
      className="flex items-center gap-2 rounded-full border border-[var(--border-hi)]
        px-3 py-1 type-small text-[var(--text-dim)]
        hover:text-[var(--text)] hover:border-[var(--text)] transition-colors"
    >
      <span
        aria-hidden="true"
        style={value ? { background: accent, borderColor: accent } : undefined}
        className={`w-1.5 h-1.5 rounded-full border transition-colors ${
          value ? '' : 'border-[var(--text-dim)] bg-transparent'
        }`}
      />
      {children}
    </button>
  )
}
