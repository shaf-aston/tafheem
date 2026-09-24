/**
 * Failure banner. role="alert" so it is announced the moment it appears.
 *
 * `inline` puts the title and the reason on one line, title left, reason
 * right, for a failure inside a section rather than across a page: the
 * stacked shape stood as tall as the diagram it was standing in for.
 */
export default function ErrorAlert({ title, children, inline = false }) {
  return (
    <div
      role="alert"
      aria-live="assertive"
      className={`rise-in rounded-[var(--radius-md)] text-sm border ${
        inline ? 'px-4 py-2 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1' : 'p-4 space-y-2'
      }`}
      style={{
        borderColor: 'color-mix(in srgb, var(--danger) 40%, transparent)',
        background: 'color-mix(in srgb, var(--danger) 10%, transparent)',
        color: 'var(--danger)',
      }}
    >
      {title && <div className="font-semibold">{title}</div>}
      <div className={`text-[var(--text-dim)] ${inline ? 'text-right flex flex-col items-end' : ''}`}>{children}</div>
    </div>
  )
}
