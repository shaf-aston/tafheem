/** A short notice with one way back, fixed to the foot of the screen. Shown only while `message` is set. */
export default function UndoToast({ message, onUndo, undoLabel = 'Undo' }) {
  if (!message) return null
  return (
    <div role="status"
      className="rise-in fixed start-1/2 -translate-x-1/2 bottom-4 max-sm:bottom-[calc(var(--layout-nav)+1rem)] z-[var(--layer-popover)]
        flex items-center gap-3 ps-4 pe-1 rounded-full border border-[var(--border-hi)] bg-[var(--surface-hi)] shadow-[var(--shadow-pop)]">
      <span className="type-ui">{message}</span>
      <button type="button" onClick={onUndo}
        className="press min-h-11 px-4 rounded-full font-bold text-[var(--primary-hi)]">{undoLabel}</button>
    </div>
  )
}
