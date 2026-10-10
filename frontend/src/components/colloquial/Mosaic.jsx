// The lesson's phrases as a mosaic; every FEATURE_EVERY-th tile is a large one.
import settings from '../../colloquial.json'
import Face, { FOCUS } from './Face'

const FEATURE_EVERY = settings['feature-every']

export default function Mosaic({ phrases, onOpen }) {
  return (
    <ul className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2 sm:gap-3">
      {phrases.map((phrase, i) => {
        const big = i % FEATURE_EVERY === 0
        return (
          <li key={phrase.arabic + phrase.english} className={big ? 'col-span-2 sm:row-span-2' : ''}>
            <button
              type="button"
              onClick={() => onOpen(i)}
              aria-label={`${phrase.english} (${phrase.arabic})`}
              className={`press group block w-full h-full rounded-[var(--radius-md)] border border-[var(--border)]
                hover:border-[var(--border-hi)] overflow-hidden transition-colors ${FOCUS}`}
            >
              <Face
                phrase={phrase}
                index={i}
                arabicSize={big ? 'lg' : 'sm'}
                className={big ? 'aspect-[2/1] sm:aspect-auto sm:h-full' : 'aspect-[4/5] sm:aspect-square'}
              />
            </button>
          </li>
        )
      })}
    </ul>
  )
}
