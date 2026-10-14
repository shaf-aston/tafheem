/** Teach card for a hadith: its key line in Arabic and English, the whole hadith on request, the source. */
import ArabicText from '../../ui/ArabicText'
import Disclosure from '../../ui/Disclosure'
import { sayIn } from '../../../lib/say'

const say = sayIn('en')

export default function HadithCard({ card }) {
  const { hadith } = card
  return (
    <div className="grow-card grow-teach">
      <span className="grow-card-tag">{say(card.tag)} · {say('{n} of 42', { n: hadith.n })}</span>
      <ArabicText as="p" size="lg" className="grow-teach-ar">{hadith.key.ar}</ArabicText>
      <p className="grow-teach-en grow-teach-line">{hadith.key.en}</p>
      <Disclosure label={say('The whole hadith')}>
        <div className="grow-whole">
          <ArabicText as="p" size="base">{hadith.arabic}</ArabicText>
          <p>{hadith.english}</p>
          <p className="grow-hint">{say('An-Nawawi’s Forty, hadith {n}, from sunnah.com via fawazahmed0/hadith-api', { n: hadith.n })}</p>
        </div>
      </Disclosure>
    </div>
  )
}
