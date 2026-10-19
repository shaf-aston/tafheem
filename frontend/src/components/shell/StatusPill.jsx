/** The backend's state in the header: a dot, and on a wide screen three words. */
const STATUS = {
  checking: { color: 'var(--tab-dict)',  label: 'Connecting…', pulse: true },
  ok:       { color: 'var(--success)',   label: 'Backend Ready' },
  error:    { color: 'var(--danger)',    label: 'Backend offline' },
}

export default function StatusPill({ status, nlpEngine, aiBackend, ear }) {
  const { color, label, pulse } = STATUS[status]

  // Engine names are for whoever runs the thing, not for whoever reads Arabic
  // with it. The dot and three words say whether it is up; the names stay in
  // the tooltip for anyone who wants them.
  const engines = [nlpEngine, aiBackend, ear].filter(Boolean).join(' + ')

  return (
    <div
      className="flex items-center gap-2 type-small text-[var(--text-dim)]"
      aria-live="polite"
      title={engines ? `Engines: ${engines}` : undefined}
    >
      <span
        className={`w-2 h-2 rounded-full shrink-0 ${pulse ? 'animate-pulse' : ''}`}
        style={{ background: color, boxShadow: `0 0 8px ${color}` }}
      />
      {/* Dot only on a phone: the full label plus the command bar and gear
          overflows a 375px screen and scrolls the whole page sideways. */}
      <span className="sr-only sm:not-sr-only">{label}</span>
    </div>
  )
}
