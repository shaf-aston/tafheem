/** The round ✕ that closes a sheet. Placement comes from `className`. */
export default function CloseButton({ className = '', ...props }) {
  return (
    <button
      type="button"
      aria-label="Close"
      className={`press w-9 h-9 grid place-items-center rounded-full border border-[var(--border-hi)] text-[var(--text)] ${className}`}
      {...props}
    >
      <span aria-hidden="true">✕</span>
    </button>
  )
}
