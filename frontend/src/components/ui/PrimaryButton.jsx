/**
 * The one action that finishes a step. Its colour is the active panel's accent,
 * passed in as a token value rather than chosen from a list of class names here,
 * so adding a panel colour needs no change to this file.
 */
export default function PrimaryButton({
  accent = 'var(--primary)',
  disabled,
  onClick,
  loading = false,
  children,
  type = 'button',
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      style={{
        '--c': accent,
        background: disabled ? 'var(--surface)' : accent,
        color: disabled ? 'var(--text-faint)' : 'var(--bg)',
      }}
      className={`w-full py-3 rounded-[var(--radius-md)] font-semibold text-sm
        flex items-center justify-center gap-2
        transition-[filter] duration-[calc(var(--motion-instant-ms)*1ms)]
        ${disabled ? 'cursor-not-allowed' : 'glow press hover:brightness-110'}`}
    >
      {loading && (
        <span
          aria-hidden="true"
          className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin shrink-0"
        />
      )}
      {children}
    </button>
  )
}
