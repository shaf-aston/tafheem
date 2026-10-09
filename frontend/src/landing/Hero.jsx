import { scrollToEl } from '../lib/scrollToEl'
import links from './links.json'
import AyahDiagram from './AyahDiagram.jsx'
import ayah from './assets/ayahDiagram.json'

// Exactly one screen: the promise on the left, an ayah building its grammar on
// the right. The hero only places the diagram; the diagram sizes itself.
export default function Hero() {
  return (
    <section className="hero" id="hero">
      <div className="hero-grid">
        <div className="hero-copy">
          <p className="eyebrow label">Tafheem</p>
          <h1 className="headline">
            Read the Qur&apos;an.<br />
            <span className="accent">Understand</span><br />
            every word.
          </h1>
          <div className="cta-row">
            <a href={links.tool} className="cta">See it in action</a>
            <button
              type="button"
              className="cta ghost"
              onClick={() => scrollToEl(document.getElementById('story'), 'top')}
            >
              How it works
            </button>
          </div>
        </div>
        <div className="hero-stage">
          <AyahDiagram ayah={ayah} />
        </div>
      </div>
    </section>
  )
}
