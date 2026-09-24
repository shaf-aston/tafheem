const SOURCES = [
  "Lisan al-Arab", "Taj al-Arus", "Lane's Lexicon", 'Maqayis al-Lugha', '34 classical books',
  'Ibn Faris', 'sunnah.com', "Qur'an corpus", 'Tafsir sources', 'OpenITI',
]

function Track({ reverse }) {
  const items = [...SOURCES, ...SOURCES]
  return (
    <div className="marquee" style={reverse ? { marginTop: '1rem' } : undefined}>
      <div className={`m-track${reverse ? ' rev' : ''}`}>
        {items.map((s, i) => (
          <span className="m-item" key={s + i}><b>{s}</b></span>
        ))}
      </div>
    </div>
  )
}

// Two CSS-animated tracks running opposite directions, pausing on hover.
// prefers-reduced-motion freezes them via the global rule in landing.css.
export default function SourcesMarquee() {
  return (
    <section className="marquee-section">
      <p className="m-label label">Trusted sources, not guesses</p>
      <Track />
      <Track reverse />
    </section>
  )
}
