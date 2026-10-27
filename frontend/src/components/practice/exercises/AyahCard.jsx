/** Teach card for an ayah: its Arabic and English, which surah and where. */
import ArabicText from '../../ui/text/ArabicText'
import { sayIn } from '../../../lib/text/say'

const say = sayIn('en')

export default function AyahCard({ card }) {
  const { ayah } = card
  return (
    <div className="grow-card grow-teach">
      <span className="grow-card-tag">{say(card.tag)}</span>
      <ArabicText as="p" size="lg" className="grow-teach-ar">{ayah.arabic}</ArabicText>
      <p className="grow-teach-en grow-teach-line">{ayah.english}</p>
      <p className="grow-hint">{say('{name} · ayah {n}', { name: ayah.name_en, n: ayah.ayah })}</p>
    </div>
  )
}
