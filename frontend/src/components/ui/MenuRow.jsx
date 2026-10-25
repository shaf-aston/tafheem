/**
 * One row of a sheet menu: a picture in a tinted tile, the name with a
 * one-line hint under it, and at the end a count or a tick. The row that is
 * open wears the accent. Colour comes from `accent`; the picture is any
 * TopicIcon key. Sized for a thumb (--layout-tap-min via .tap).
 */
import TopicIcon from './TopicIcon'

export default function MenuRow({ icon, label, hint, count, picked, accent, onClick }) {
  return (
    <button
      type="button"
      aria-pressed={picked}
      onClick={onClick}
      style={{ '--c': accent }}
      className={`press tap w-full min-h-16 px-3 py-2 flex items-center gap-3 rounded-[var(--radius-sm)] border text-start transition-colors ${
        picked ? 'border-[var(--c)] bg-[var(--surface-hi)]' : 'border-transparent hover:bg-[var(--surface-hi)]'
      }`}
    >
      <span
        aria-hidden="true"
        className="shrink-0 w-11 h-11 grid place-items-center rounded-[var(--radius-sm)] text-[var(--c)] bg-[color-mix(in_srgb,var(--c)_14%,transparent)]"
      >
        <TopicIcon topic={icon} className="w-6 h-6" />
      </span>
      <span className="flex-1 min-w-0 flex flex-col">
        <span className={`type-body ${picked ? 'text-[var(--c)]' : 'text-[var(--text)]'}`}>{label}</span>
        {hint && <span className="type-small text-[var(--text-faint)]">{hint}</span>}
      </span>
      {count > 0 && (
        <span className="shrink-0 min-w-6 px-2 py-0.5 rounded-full text-center type-small tabular-nums text-[var(--c)] bg-[color-mix(in_srgb,var(--c)_14%,transparent)]">{count}</span>
      )}
      {picked && <span aria-hidden="true" className="shrink-0 text-[var(--c)]">✓</span>}
    </button>
  )
}
