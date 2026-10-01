// Native select in the shared rounded-pill look; sites add size, padding and colour via className.
export default function PillSelect({ className = '', children, ...rest }) {
  return (
    <select
      className={`rounded-full bg-[var(--surface)] border focus:border-[var(--c)] focus:outline-none transition-colors ${className}`}
      {...rest}
    >
      {children}
    </select>
  )
}
