import { useModal } from '../lib/useModal'

import TarkeebDiagram from './TarkeebDiagram'
import CloseButton from './ui/CloseButton'
import Tooltip from './ui/Tooltip'

/**
 * A tarkeeb diagram in its card. When any word was left open, a line underneath
 * says how much was placed, so a tidy picture never implies everything was;
 * `openWhy`, when given, explains in a hover who left it open. `view`
 * (useTarkeebView) is set from the controls in the header above, which also
 * open the same diagram larger, filling the screen.
 */
export default function TarkeebFigure({ tarkeeb, openWhy, view }) {
  // A book's own worked example carries no coverage: the book placed every word.
  const { coverage = 1 } = tarkeeb
  const { big, setBig, mode } = view
  const dialog = useModal(big)
  const placed = Math.round(coverage * 100)
  const open = openWhy
    ? <Tooltip text={openWhy}><span className="underline decoration-dotted cursor-help">left open</span></Tooltip>
    : 'left open'
  const diagram = <TarkeebDiagram tarkeeb={tarkeeb} mode={mode} />
  return (
    <div className="space-y-2">
      <div
        className="rise-in p-5 rounded-[var(--radius-lg)] bg-[var(--surface)]
          border border-[var(--border)]"
      >
        {diagram}
      </div>
      {coverage < 1 && (
        <p className="text-center type-small text-[var(--text-faint)]">
          {placed}% of the words placed, the rest {open}
        </p>
      )}
      <dialog
        ref={dialog}
        aria-label="Tarkeeb, larger"
        onClose={() => setBig(false)}
        onClick={(e) => e.target === dialog.current && setBig(false)}
        className="tk-max"
      >
        {big && (
          <div className="tk-max-box">
            <CloseButton className="tk-max-close" onClick={() => setBig(false)} />
            {diagram}
          </div>
        )}
      </dialog>
    </div>
  )
}
