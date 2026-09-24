import Reveal from './Reveal.jsx'
import { quranFolio } from './assets/clips.js'

// Full-bleed manuscript image with a scroll-linked parallax handled entirely
// in CSS (animation-timeline: view()), matching the prototype.
export default function FolioBand() {
  return (
    <section className="manu">
      <img
        className="manu-img"
        src={quranFolio}
        alt="A page from a Qur'an manuscript"
        loading="lazy"
      />
      <div className="manu-overlay" />
      <Reveal as="div" className="manu-content">
        <p className="manu-quote">
          Recite out loud. Every word is heard, and the ear was tested on 1,950 real recitations.
        </p>
        <p className="manu-cite">Qur&apos;an manuscript &middot; Photo: Marie-Lan Nguyen, CC BY</p>
      </Reveal>
    </section>
  )
}
