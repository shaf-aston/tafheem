/** Recovery action inside an ErrorAlert, every failure offers a way forward. */
export default function RetryButton({ onClick, label = 'Try again' }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="mt-3 inline-flex items-center gap-1.5 text-xs rounded-[var(--radius-sm)] px-2.5 py-1 border transition-colors"
      style={{
        borderColor: 'color-mix(in srgb, var(--danger) 40%, transparent)',
        color: 'var(--danger)',
      }}
    >
      <span aria-hidden="true">↺</span> {label}
    </button>
  )
}
