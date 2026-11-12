/**
 * All sections: every tab under its group, opened from the end of the strip.
 * A kept-mounted BottomSheet, as Settings is: Esc, backdrop and focus trap come free, and Edit bar survives a close.
 */
import { useState } from 'react'

import { ahead } from '../../lib/api/warm'
import { useDrag } from '../../lib/shell/useDrag'
import BottomSheet from '../ui/overlays/BottomSheet'
import ArabicText from '../ui/text/ArabicText'
import CloseButton from '../ui/buttons/CloseButton'
import TabGroups from '../ui/inputs/TabGroups'
import Tile from '../ui/display/Tile'
import DockSlots from './DockSlots'

// `dock` is the ids on the phone bar, `onDock(id, slot)` changes it (lib/nav/dock.js);
// both left out, there is no bar to edit; `size` is how many tab places the bar has.
// Editing is the phone's: the strip a wider screen has is its own rule.
export default function SectionsMenu({ open, onClose, groups, tabs, colorOf, onGo, here, dock, onDock, size: places = 0, onHover, children }) {
  const [editing, setEditing] = useState(false)
  const editable = Boolean(dock)
  const size = editable ? Math.max(dock.length, places) : 0
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
    <BottomSheet
      open={open}
      onClose={close}
      labelledBy="sections-title"
      width="wide"
      className="p-5 space-y-5 max-h-[88dvh] overflow-y-auto"
    >
        <div className="flex items-center justify-between gap-2">
          <h2 id="sections-title" className="type-head type-lead font-bold text-[var(--text)]">All sections</h2>
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
            {/* The round ✕ every other sheet closes with (Settings, Study, the profile). */}
            <CloseButton onClick={close} />
          </div>
        </div>
        {editing && (
          <section className="sm:hidden sticky top-0 z-[var(--layer-sticky)] -mt-2 pt-2 pb-3 space-y-2 bg-[var(--surface)] border-b border-[var(--border)]">
            <h3 className="type-small text-[var(--text-faint)]">On the bar</h3>
            <DockSlots size={size} tabs={dock.map((id) => tabs.find((tab) => tab.id === id))} colorOf={colorOf} drag={drag} grip={grip} />
            <p className="type-small text-[var(--text-faint)]">Drag a tab to a place on the bar, or back down to leave it. Or tap one to pin it.</p>
          </section>
        )}
        {/* Dropping a tab anywhere in here sends it off the bar. */}
        <div data-slot="more" className="space-y-5">
          <TabGroups groups={groups} tabs={tabs} grid="grid-cols-2 sm:grid-cols-3 gap-2">
            {(tab, index) => (
              <div
                key={tab.id}
                aria-current={tab.id === here ? 'page' : undefined}
                className={`flex items-stretch gap-1 ${drag?.id === tab.id ? 'opacity-40' : ''}`}
              >
                <Tile
                  variant="chip"
                  accent={colorOf(tab.id)}
                  onClick={() => tap(tab.id)}
                  {...ahead(() => onHover?.(tab.id))}
                  aria-pressed={editing ? onBar(tab.id) : undefined}
                  style={{ '--i': index }}
                  className={`flex-1 min-w-0 ${tab.id === here || (editing && onBar(tab.id)) ? 'border-[var(--c)]' : ''}`}
                >
                  <span className="flex items-center gap-2 type-ui font-semibold">
                    <span aria-hidden="true" className="w-2.5 h-2.5 rounded-full shrink-0 bg-[var(--c)]" />
                    <span>{tab.label}</span>
                  </span>
                  <ArabicText size="lg" className="shrink-0 leading-tight text-[var(--c)]">{tab.arabic}</ArabicText>
                </Tile>
                {editing && (
                  <span
                    {...grip(tab.id)}
                    role="img"
                    aria-label={`Drag ${tab.label} to the bar`}
                    className="grid place-items-center w-9 shrink-0 rounded-[var(--radius-sm)] border border-[var(--border)] text-[var(--text-faint)] cursor-grab"
                  >
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
                      <circle cx="9" cy="6" r="1.6" /><circle cx="15" cy="6" r="1.6" />
                      <circle cx="9" cy="12" r="1.6" /><circle cx="15" cy="12" r="1.6" />
                      <circle cx="9" cy="18" r="1.6" /><circle cx="15" cy="18" r="1.6" />
                    </svg>
                  </span>
                )}
              </div>
            )}
          </TabGroups>
          {children}
        </div>
      {drag && (
        <div
          aria-hidden="true"
          style={{ left: drag.x, top: drag.y, '--c': colorOf(drag.id) }}
          className="fixed z-[var(--layer-tip)] -translate-x-1/2 -translate-y-full pointer-events-none px-3 py-1.5 rounded-[var(--radius-sm)]
            border border-[var(--c)] bg-[var(--surface-hi)] text-[var(--c)] type-small font-semibold shadow-[var(--shadow-lift)]"
        >
          {tabs.find((tab) => tab.id === drag.id)?.label}
        </div>
      )}
    </BottomSheet>
  )
}
