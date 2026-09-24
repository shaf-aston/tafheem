import Reveal from './Reveal.jsx'

export default function Finale() {
  return (
    <section className="finale">
      <div className="wrap">
        <Reveal as="p" className="kufi arabic" lang="ar" dir="rtl">العربية</Reveal>
        <Reveal as="p">Arabic, unlocked. Grammar you can see. Recitation you can trust.</Reveal>
        <a href="/app" className="cta">Open the tool</a>
      </div>
    </section>
  )
}
