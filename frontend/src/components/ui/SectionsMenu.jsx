/**
 * All sections: every tab under its group, opened from the end of the strip.
 * Native <dialog>, as in SettingsPanel: Esc, backdrop and focus trap come free.
 */
import { useEffect, useRef } from 'react'

import ArabicText from './ArabicText'

export default function SectionsMenu({ open, onClose, groups, tabs, colorOf, onGo, here }) {
  const dialog = useRef(null)

  useEffect(() => {
    const element = dialog.current
    if (!element) return
    if (open && !element.open) element.showModal()
    if (!open && element.open) element.close()
  }, [open])

  const go = (id) => {
    onClose()
    onGo(id)
  }

  return (
    <dialog
      ref={dialog}
      onClose={onClose}
      onClick={(e) => e.target === dialog.current && onClose()}
      aria-labelledby="sections-title"
      className="m-auto p-0 bg-transparent max-w-[min(44rem,92vw)] w-full"
    >
      <div
        className="rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)]
          p-5 space-y-5 max-h-[88vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="sections-title" className="text-base font-bold text-[var(--text)]">All sections</h2>
        {groups.map((group) => (
          <section key={group.id} className="space-y-2">
            <h3 className="type-small text-[var(--text-faint)]">{group.label}</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {tabs.filter((tab) => tab.group === group.id).map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => go(tab.id)}
                  aria-current={tab.id === here ? 'page' : undefined}
                  style={{ '--c': colorOf(tab.id) }}
                  className="flex items-center justify-between gap-2 min-h-11 px-3 text-left
                    rounded-[var(--radius-sm)] border bg-[var(--bg)] border-[var(--border)]
                    hover:border-[var(--border-hi)] aria-[current=page]:border-[var(--c)]"
                >
                  <span className="type-body font-medium text-[var(--c)]">{tab.label}</span>
                  <ArabicText className="text-[var(--text-faint)]">{tab.arabic}</ArabicText>
                </button>
              ))}
            </div>
          </section>
        ))}
      </div>
    </dialog>
  )
}
