import { fill, whereOf } from '../../lib/similar/similar'
import { ahead } from '../../lib/api/warm'
import copy from '../../config/similar.json'

const LABEL = { new: copy['label-new'], due: copy['label-due'], known: copy['label-known'] }
const TONE = { new: 'var(--text-faint)', due: 'var(--primary-hi)', known: 'var(--success)' }

/**
 * The surah's pairs, one button each, with where each stands. Always a column:
 * on a wide screen it is the rail and scrolls inside it; on a phone it is the
 * Browse sheet's body (SimilarPanel), never a strip of hundreds of chips.
 * `onAhead` fetches a pair before it is chosen (hover, press, focus).
 */
export default function PairList({ pairs, chosen, onChoose, onAhead, standing, className = '' }) {
  return (
    <ul className={`flex flex-col gap-1.5 ${className}`}>
      {pairs.map((pair) => {
        const state = standing(pair.id)
        return (
          <li key={pair.id}>
            <button
              type="button"
              onClick={() => onChoose(pair.id)}
              {...ahead(() => onAhead?.(pair))}
              aria-current={pair.id === chosen || undefined}
              className={`w-full text-left rounded-[var(--radius-sm)] border px-3 py-2 min-h-[var(--layout-tap-min)] hover:bg-[var(--surface-hi)] ${pair.id === chosen ? 'border-[var(--border-hi)] bg-[var(--surface-hi)]' : 'border-transparent'}`}
            >
              <span className="flex items-center justify-between gap-3">
                <span className="type-ui font-semibold text-[var(--text)]">{pair.mine}</span>
                <span className="type-label" style={{ color: TONE[state] }}>{LABEL[state]}</span>
              </span>
              <span className="block type-label text-[var(--text-dim)]">{fill(copy.twin, { where: whereOf(pair.twin) })}</span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
