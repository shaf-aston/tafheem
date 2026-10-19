/** The three dots that mean "more": the bottom bar's More and every menu of extras wear the same mark. */
export default function MoreIcon({ size = 22 }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round">
      <path d="M6 12h.01M12 12h.01M18 12h.01" />
    </svg>
  )
}
