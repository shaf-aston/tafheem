/**
 * The command line, in the header, on every page.
 *
 * No dim and no modal on purpose: it is a control in the page, not a thing that
 * happens to the page. Idle it is a narrow box; focused it grows in place and
 * the results open under it, so the page never jumps.
 *
 * Typing autocompletes a tab name like a terminal does, in grey ahead of the
 * cursor, and Tab accepts it. "/" names a tab, "@" looks a root up, "2:255" is
 * an ayah, anything else goes to the analyser. Every answer comes from what is
 * already known on this machine, so there is nothing to wait for.
 */
import { useEffect, useRef, useState } from 'react'

import { useCommandLine } from '../../lib/useCommandLine'
import CommandField from './CommandField'
import CommandResults from './CommandResults'

const NAME = 'cb'
// The badge says the shortcut in the reader's own dialect.
const MAC = /Mac/.test(navigator.platform ?? '')
const KEY_LABEL = MAC ? '⌘K' : 'Ctrl K'

export default function CommandBar({ tabs, colorOf, onGo }) {
  const [open, setOpen] = useState(false)
  const input = useRef(null)
  const line = useCommandLine(tabs, (row) => {
    setOpen(false)
    input.current?.blur()
    onGo(row.tabId, row.value)
  }, {
    // Escape with text typed clears it (the hook's rule); with the line
    // already empty it hands the header its focus back.
    onEscape: () => input.current?.blur(),
  })

  // Ctrl+K from anywhere. The number keys already jump tabs, so this is the one
  // shortcut that has to work while another control has focus.
  useEffect(() => {
    const onKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        // The launcher has a line of its own; pulling focus back to the header
        // would type into a box nobody can see.
        if (document.querySelector('dialog[open]')) return
        e.preventDefault()
        input.current?.focus()
        input.current?.select()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  const showing = open && line.rows.length > 0

  return (
    <div className="cb" data-open={open ? 'true' : undefined} onBlur={(e) => {
      if (!e.currentTarget.contains(e.relatedTarget)) setOpen(false)
    }}>
      <CommandField
        line={line}
        name={NAME}
        inputRef={input}
        placeholder="Search or ask"
        onFocus={() => setOpen(true)}
        showing={showing}
        trailing={!line.query && <kbd className="cb-key">{KEY_LABEL}</kbd>}
      />

      {showing && (
        <CommandResults
          id={`${NAME}-results`}
          name={NAME}
          rows={line.rows}
          tabs={tabs}
          colorOf={colorOf}
          active={line.active}
          onHover={line.setActive}
          onPick={line.run}
          railTab={line.rows[line.active]?.tabId}
          onRail={(id) => { setOpen(false); input.current?.blur(); onGo(id) }}
        />
      )}
    </div>
  )
}
