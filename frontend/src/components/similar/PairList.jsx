import { fill, whereOf } from '../../lib/similar'
import copy from '../../similar.json'

const LABEL = { new: copy['label-new'], due: copy['label-due'], known: copy['label-known'] }
const TONE = { new: 'var(--text-faint)', due: 'var(--primary-hi)', known: 'var(--success)' }

/** The surah's pairs, one button each, with where each stands. */
export default function PairList({ pairs, chosen, onChoose, standing }) {
  return (
    <ul className="flex lg:flex-col gap-1.5 overflow-x-auto lg:overflow-visible pb-1 lg:pb-0">
      {pairs.map((pair) => {
        const state = standing(pair.id)
        return (
          <li key={pair.id} className="shrink-0 lg:shrink">
            <button
              type="button"
              onClick={() => onChoose(pair.id)}
              aria-current={pair.id === chosen || undefined}
              className={`w-full text-left rounded-[var(--radius-sm)] border px-3 py-2 hover:bg-[var(--surface-hi)] ${pair.id === chosen ? 'border-[var(--border-hi)] bg-[var(--surface-hi)]' : 'border-transparent'}`}
            >
              <span className="flex items-center justify-between gap-3">
                <span className="type-small font-semibold text-[var(--text)]">{pair.mine}</span>
                <span className="type-tiny" style={{ color: TONE[state] }}>{LABEL[state]}</span>
              </span>
              <span className="block type-tiny text-[var(--text-dim)]">{fill(copy.twin, { where: whereOf(pair.twin) })}</span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
