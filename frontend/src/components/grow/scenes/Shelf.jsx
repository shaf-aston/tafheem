/** The Hadith world's picture, The Library: a spine per hadith, filled when known; tap one for its key line. */
import { useState } from 'react'

import { sayIn } from '../../../lib/text/say'
import ArabicText from '../../ui/text/ArabicText'

const say = sayIn('en')
const LABELS = { known: 'learnt', learning: 'learning', new: 'not met yet' }

export default function Shelf({ items }) {
  const [picked, pick] = useState(null)
  const shown = items.find((one) => one.key === picked) ?? items.find((one) => one.status !== 'known') ?? items[0]
  const known = items.filter((one) => one.status === 'known').length
  return (
    <div className="grow-shelf">
      <div className="grow-spines">
        {items.map(({ key, item, status }) => (
          <button key={key} type="button" className="grow-spine" data-s={status} aria-pressed={key === shown?.key}
            aria-label={say('Hadith {n}, {status}', { n: item.n, status: say(LABELS[status]) })} onClick={() => pick(key)}>
            {item.n}
          </button>
        ))}
      </div>
      {shown && (
        <div className="grow-shelf-line" aria-live="polite">
          <span className="grow-card-tag">{say('Hadith {n}', { n: shown.item.n })}</span>
          <ArabicText as="p" size="base">{shown.item.key.ar}</ArabicText>
          <p>{shown.item.key.en}</p>
        </div>
      )}
      <p className="grow-hint tabular-nums">{say('{known} of {total} on the shelf', { known, total: items.length })}</p>
    </div>
  )
}
