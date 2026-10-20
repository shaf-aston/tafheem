/**
 * The one action that finishes a step, drawn as the call to action (.cta in
 * styles/components.css): a pill in the active panel's accent. The colour is
 * passed in as a token value rather than chosen from a list of class names
 * here, so adding a panel colour needs no change to this file.
 */
export default function PrimaryButton({
  accent = 'var(--primary)',
  disabled,
  onClick,
  loading = false,
  children,
  type = 'button',
  ref,
}) {
  return (
    <button
      ref={ref}
      type={type}
      onClick={onClick}
      disabled={disabled}
      style={{ '--c': accent, '--cta-fill': accent }}
      className={`cta w-full py-3 text-sm ${disabled ? '' : 'glow'}`}
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
