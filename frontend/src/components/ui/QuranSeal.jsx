/**
 * The faint round seal behind the Quran tab: "القرآن الكريم" set inside a beaded ring,
 * as a mushaf cover is stamped. Decoration only, so screen readers skip it.
 * Its colour and strength are theme tokens (--backdrop-ink, --backdrop-strength),
 * so a light theme only has to change those two values.
 */
/** A bead every 15 degrees round the ring, the ones on the eight main points larger. */
const BEADS = Array.from({ length: 24 }, (_, i) => i * 15)

export default function QuranSeal({ className = '' }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 400 400" className={`quran-seal ${className}`.trim()}>
      <defs>
        <linearGradient id="quran-seal-sheen" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="currentColor" stopOpacity="1" />
          <stop offset="0.5" stopColor="currentColor" stopOpacity="0.55" />
          <stop offset="1" stopColor="currentColor" stopOpacity="0.9" />
        </linearGradient>
      </defs>
      <g fill="url(#quran-seal-sheen)" stroke="url(#quran-seal-sheen)">
        <circle cx="200" cy="200" r="190" fill="none" strokeWidth="1.5" />
        <circle cx="200" cy="200" r="182" fill="none" strokeWidth="0.75" />
        <circle cx="200" cy="200" r="132" fill="none" strokeWidth="0.75" />
        {BEADS.map((deg) => (
          <circle key={deg} cx="200" cy="50" r={deg % 45 ? 2 : 3.5} stroke="none" transform={`rotate(${deg} 200 200)`} />
        ))}
        <text lang="ar" direction="rtl" x="200" y="196" fontSize="72" textAnchor="middle" stroke="none" className="quran-seal-script">
          القرآن
        </text>
        <text lang="ar" direction="rtl" x="200" y="262" fontSize="52" textAnchor="middle" stroke="none" className="quran-seal-script">
          الكريم
        </text>
      </g>
    </svg>
  )
}
