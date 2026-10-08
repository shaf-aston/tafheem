import Segmented from './ui/Segmented'
import { colorFor } from '../theme'

const GHAIR_AAMIL_ACCENT = colorFor('role', 'ghair_aamil')
const MODES = [
  { id: 'merged', label: 'Merged' },
  { id: 'split', label: 'Split' },
]

/**
 * The chart's controls, for the header beside its Copy button: show larger, and
 * Merged or Split where a written word was cut into pieces. `view` is useTarkeebView's.
 */
export default function TarkeebTools({ view }) {
  return (
    <>
      <button
        type="button"
        aria-label="Show larger"
        title="Show larger"
        onClick={() => view.setBig(true)}
        className="press tap shrink-0 px-3 py-2 text-xs rounded-[var(--radius-md)] border border-[var(--border)] text-[var(--text-dim)]"
      >
        <span aria-hidden="true">⤢</span>
      </button>
      {view.canSplit && (
        <Segmented
          compact
          label="Show each piece written onto a word in its own column, or the written word whole"
          value={view.mode}
          onChange={view.setMode}
          accent={GHAIR_AAMIL_ACCENT}
          options={MODES}
        />
      )}
    </>
  )
}
