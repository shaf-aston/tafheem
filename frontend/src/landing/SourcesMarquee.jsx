import { useInView } from '../lib/useInView'

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

// Two CSS-animated tracks running opposite directions, pausing on hover and
// offscreen (phones feel every running layer while scrolling elsewhere).
// prefers-reduced-motion freezes them via the global rule in landing.css.
export default function SourcesMarquee() {
  const [ref, inView] = useInView({ once: false })
  return (
    <section className="marquee-section" ref={ref} data-off={!inView || undefined}>
      <p className="m-label label">Trusted sources, not guesses</p>
      <Track />
      <Track reverse />
    </section>
  )
}
