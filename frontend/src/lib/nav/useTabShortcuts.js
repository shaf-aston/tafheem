/**
 * Number keys jump between panels: 1 is the first tab, 7 the last.
 *
 * Ignored while typing, while a modifier is held, and while a dialog is open;
 * a dialog is a conversation of its own, and switching the tab behind one
 * would leave the reader looking at a panel they never asked for.
 */
import { useEffect } from 'react'

export function useTabShortcuts(tabs, onSelect) {
  useEffect(() => {
    const onKeyDown = (e) => {
      const tag = document.activeElement?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || e.metaKey || e.ctrlKey || e.altKey) return
      if (document.querySelector('dialog[open]')) return
      const index = Number.parseInt(e.key, 10) - 1
      if (index >= 0 && index < tabs.length) onSelect(tabs[index].id)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [tabs, onSelect])
}
