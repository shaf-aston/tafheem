/**
 * The quiet secondary action beside a primary one: Back, Skip, Redo, "See it
 * in the notes". One component so Tamreen and the notes cannot drift into two
 * looks for the same role.
 */
import { forwardRef } from 'react'

const SmallButton = forwardRef(function SmallButton({ className = '', ...props }, ref) {
  return (
    <button
      ref={ref}
      type="button"
      className={`press type-small px-3 py-1.5 rounded-[var(--radius-sm)] border border-[var(--border)]
        hover:border-[var(--border-hi)] transition-colors disabled:opacity-40 ${className}`}
      {...props}
    />
  )
})

export default SmallButton
