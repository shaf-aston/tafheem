import TarkeebDiagram from './TarkeebDiagram'
import Tooltip from './ui/Tooltip'

/**
 * A tarkeeb diagram in its card. When any word was left open, a line underneath
 * says how much was placed, so a tidy picture never implies everything was;
 * `openWhy`, when given, explains in a hover who left it open.
 */
export default function TarkeebFigure({ words, tree, unwritten, coverage, openWhy }) {
  const placed = Math.round((coverage ?? 0) * 100)
  const open = openWhy
    ? <Tooltip text={openWhy}><span className="underline decoration-dotted cursor-help">left open</span></Tooltip>
    : 'left open'
  return (
    <div className="space-y-2">
      <div
        className="rise-in p-5 rounded-[var(--radius-lg)] bg-[var(--surface)]
          border border-[var(--border)]"
      >
        <TarkeebDiagram words={words} tree={tree} unwritten={unwritten} />
      </div>
      {(coverage ?? 0) < 1 && (
        <p className="text-center type-small text-[var(--text-faint)]">
          {placed}% of the words placed, the rest {open}
        </p>
      )}
    </div>
  )
}
