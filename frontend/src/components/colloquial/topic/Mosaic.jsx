// Phrases (or a topic's words) as a mosaic; every FEATURE_EVERY-th tile is a large one
// when it has a picture to show and enough tiles surround it to fill the rows beside
// it. A tile with no picture is only as tall as its words.
// `start` numbers a later group on from the ones before it, so tiles open the right item.
import settings from '../../../config/colloquial-display.json'
import Face, { FOCUS } from '../parts/Face'

const FEATURE_EVERY = settings['feature-every']

export default function Mosaic({ phrases, onOpen, start = 0 }) {
  return (
    <ul className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2 sm:gap-3">
      {phrases.map((phrase, i) => {
        const big = i % FEATURE_EVERY === 0 && Boolean(phrase.image) && phrases.length >= FEATURE_EVERY
        return (
          <li key={phrase.arabic + phrase.english} className={big ? 'col-span-2 sm:row-span-2' : ''}>
            <button
              type="button"
              onClick={() => onOpen(start + i)}
              aria-label={`${phrase.english} (${phrase.arabic})`}
              className={`press group block w-full h-full rounded-[var(--radius-md)] border border-[var(--border)]
                hover:border-[var(--border-hi)] overflow-hidden transition-colors ${FOCUS}`}
            >
              <Face
                phrase={phrase}
                index={start + i}
                arabicSize={big ? 'lg' : 'sm'}
                className={big ? `${phrase.image.endsWith('.svg') ? 'aspect-[4/3]' : 'aspect-[2/1]'} sm:aspect-auto sm:h-full` : phrase.image ? 'aspect-[4/5] sm:aspect-square' : 'h-full min-h-24'}
              />
            </button>
          </li>
        )
      })}
    </ul>
  )
}
