/** The Quran world's picture, The Night Sky: a constellation per surah, a star per ayah, bright once known. */
import { starsOf } from '../../../lib/grow/sky'
import { sayIn } from '../../../lib/say'
import ArabicText from '../../ui/ArabicText'

const say = sayIn('en')

/** The items grouped by surah, in order. */
function surahsOf(items) {
  const groups = new Map()
  for (const entry of items) {
    if (!groups.has(entry.item.surah)) groups.set(entry.item.surah, [])
    groups.get(entry.item.surah).push(entry)
  }
  return [...groups.values()]
}

function Constellation({ entries }) {
  const { surah, name_en, name_ar } = entries[0].item
  const stars = starsOf(entries.length, surah)
  const lit = stars.filter((_, i) => entries[i].status === 'known')
  const known = lit.length
  return (
    <figure className="grow-constellation">
      <svg viewBox="0 10 100 40" role="img" aria-label={say('{name}, {known} of {total} ayat learnt', { name: name_en, known, total: entries.length })}>
        <polyline className="grow-star-line" points={lit.map(({ x, y }) => `${x},${y}`).join(' ')} />
        {stars.map(({ x, y }, i) => <circle key={entries[i].key} className="grow-star" data-s={entries[i].status} cx={x} cy={y} r="2.4" />)}
      </svg>
      <figcaption>
        <span>{name_en}</span>
        <ArabicText size="tiny">{name_ar}</ArabicText>
        <span className="tabular-nums">{known} / {entries.length}</span>
      </figcaption>
    </figure>
  )
}

export default function Sky({ items }) {
  return (
    <div className="grow-sky">
      {surahsOf(items).map((entries) => <Constellation key={entries[0].item.surah} entries={entries} />)}
    </div>
  )
}
