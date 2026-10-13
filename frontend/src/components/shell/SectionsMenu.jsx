/**
 * All sections: every tab under its group, opened from the end of the strip.
 * Native <dialog>, as in SettingsPanel: Esc, backdrop and focus trap come free.
 */
import { useState } from 'react'

import { useDrag } from '../../lib/useDrag'
import { useModal } from '../../lib/useModal'
import ArabicText from '../ui/ArabicText'
import DockSlots from './DockSlots'

// `dock` is the ids on the phone bar, `onDock(id, slot)` changes it (lib/dock.js);
// both left out, there is no bar to edit. Editing is the phone's: the strip a
// wider screen has is its own rule.
export default function SectionsMenu({ open, onClose, groups, tabs, colorOf, onGo, here, dock, onDock, children }) {
  const dialog = useModal(open)
  const [editing, setEditing] = useState(false)
  const editable = Boolean(dock)
  const size = editable ? Math.max(dock.length, 4) : 0
  const onBar = (id) => dock?.includes(id)
  const { drag, grip } = useDrag((id, slot) => onDock(id, slot === 'more' ? null : Number(slot)))

  const close = () => {
    setEditing(false)
    onClose()
  }
  const go = (id) => {
    close()
    onGo(id)
  }
  // While editing, tapping a tab pins or unpins it instead of opening it.
  const tap = (id) => (!editing ? go(id) : onBar(id) ? onDock(id, null) : dock.length < size && onDock(id, dock.length))

  return (
    <dialog
      ref={dialog}
      onClose={close}
      onClick={(e) => e.target === dialog.current && close()}
      aria-labelledby="sections-title"
      className="sections-menu m-auto p-0 bg-transparent max-w-[min(var(--sheet-wide),92vw)] w-full"
    >
      <div
        className="rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)]
          p-5 space-y-5 max-h-[88dvh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between gap-2">
          <h2 id="sections-title" className="text-base font-bold text-[var(--text)]">All sections</h2>
          <div className="flex items-center">
            {editable && (
              <button
                type="button"
                onClick={() => setEditing((on) => !on)}
                aria-pressed={editing}
                className="tap sm:hidden min-h-11 px-3 type-small font-semibold text-[var(--text-dim)] aria-pressed:text-[var(--text)]"
              >
                {editing ? 'Done' : 'Edit bar'}
              </button>
            )}
            <button type="button" onClick={close} className="tap min-h-11 px-3 type-small font-semibold text-[var(--text-dim)]">Close</button>
          </div>
        </div>
        {editing && (
          <section className="sm:hidden sticky top-0 z-10 -mt-2 pt-2 pb-3 space-y-2 bg-[var(--surface)] border-b border-[var(--border)]">
            <h3 className="type-small text-[var(--text-faint)]">On the bar</h3>
            <DockSlots size={size} tabs={dock.map((id) => tabs.find((tab) => tab.id === id))} colorOf={colorOf} drag={drag} grip={grip} />
            <p className="type-small text-[var(--text-faint)]">Drag a tab to a place on the bar, or back down to leave it. Or tap one to pin it.</p>
          </section>
        )}
        {/* Dropping a tab anywhere in here sends it off the bar. */}
        <div data-slot="more" className="space-y-5">
          {groups.map((group) => (
            <section key={group.id} className="space-y-2">
              <h3 className="type-small text-[var(--text-faint)]">{group.label}</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {tabs.filter((tab) => tab.group === group.id).map((tab) => (
                  <div
                    key={tab.id}
                    style={{ '--c': colorOf(tab.id) }}
                    aria-current={tab.id === here ? 'page' : undefined}
                    className={`flex items-stretch rounded-[var(--radius-sm)] border bg-[var(--bg)]
                      hover:border-[var(--border-hi)] aria-[current=page]:border-[var(--c)]
                      ${editing && onBar(tab.id) ? 'border-[var(--c)]' : 'border-[var(--border)]'}
                      ${drag?.id === tab.id ? 'opacity-40' : ''}`}
                  >
                    <button
                      type="button"
                      onClick={() => tap(tab.id)}
                      aria-pressed={editing ? onBar(tab.id) : undefined}
                      className="flex flex-1 min-w-0 items-center justify-between gap-2 min-h-11 px-3 text-left"
                    >
                      <span className="type-body font-medium text-[var(--c)]">{tab.label}</span>
                      <ArabicText className="text-[var(--text-faint)]">{tab.arabic}</ArabicText>
                    </button>
                    {editing && (
                      <span
                        {...grip(tab.id)}
                        role="img"
                        aria-label={`Drag ${tab.label} to the bar`}
                        className="grid place-items-center w-9 shrink-0 border-s border-[var(--border)] text-[var(--text-faint)] cursor-grab"
                      >
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
                          <circle cx="9" cy="6" r="1.6" /><circle cx="15" cy="6" r="1.6" />
                          <circle cx="9" cy="12" r="1.6" /><circle cx="15" cy="12" r="1.6" />
                          <circle cx="9" cy="18" r="1.6" /><circle cx="15" cy="18" r="1.6" />
                        </svg>
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </section>
          ))}
          {children}
        </div>
      </div>
      {drag && (
        <div
          aria-hidden="true"
          style={{ left: drag.x, top: drag.y, '--c': colorOf(drag.id) }}
          className="fixed z-50 -translate-x-1/2 -translate-y-full pointer-events-none px-3 py-1.5 rounded-[var(--radius-sm)]
            border border-[var(--c)] bg-[var(--surface-hi)] text-[var(--c)] type-small font-semibold shadow-[var(--shadow-lift)]"
        >
          {tabs.find((tab) => tab.id === drag.id)?.label}
        </div>
      )}
    </dialog>
  )
}
