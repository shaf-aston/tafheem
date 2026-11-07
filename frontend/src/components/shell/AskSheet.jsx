/**
 * Ask: the phone bar's centre button. One box that takes anything, a word, a
 * root, an ayah number or a sentence, and sends it to the tab that answers it.
 * The same command line as the header's and Home's (useCommandLine), so it
 * routes the same way; here it rises from the bottom, where the thumb is,
 * with the box focused and the suggestions open under it.
 */
import { useEffect, useRef } from 'react'

import { useCommandLine } from '../../lib/nav/useCommandLine'
import BottomSheet from '../ui/overlays/BottomSheet'
import SheetHeader from '../ui/overlays/SheetHeader'
import CommandField from './CommandField'
import CommandResults from './CommandResults'

const NAME = 'ask'
// One of each kind it takes, so an empty box shows what to type rather than waiting.
const EXAMPLES = ['كتب', '2:255', 'ذهب الطالب إلى المدرسة']

export default function AskSheet({ tabs, colorOf, onGo, onClose }) {
  const input = useRef(null)
  const go = (tab, value) => {
    onClose()
    onGo(tab, value)
  }
  const line = useCommandLine(tabs, (row) => go(row.tabId, row.value))
  useEffect(() => { input.current?.focus() }, [])

  return (
    <BottomSheet label="Ask" onClose={onClose} className="p-4 space-y-3 min-h-[60dvh]">
      <SheetHeader onClose={onClose} className="">
        <h2 className="type-head type-lead font-bold text-[var(--text)]">Ask</h2>
      </SheetHeader>
      <div className="cb" data-wide data-open="true">
        <CommandField line={line} name={NAME} inputRef={input} placeholder="A word, root, ayah or sentence" showing={line.rows.length > 0} />
        {line.rows.length > 0 && (
          <CommandResults id={`${NAME}-results`} name={NAME} rows={line.rows} tabs={tabs} colorOf={colorOf}
            active={line.active} onHover={line.setActive} onPick={line.run}
            railTab={line.rows[line.active]?.tabId} onRail={(id) => go(id)} />
        )}
      </div>
      {!line.query && (
        <div className="flex flex-wrap gap-2 pt-1" aria-label="Try one">
          {EXAMPLES.map((text) => (
            <button key={text} type="button" onClick={() => { line.type(text); input.current?.focus() }} dir="auto"
              className="tap px-3 rounded-full border border-[var(--border-hi)] type-ui text-[var(--text-dim)]">{text}</button>
          ))}
        </div>
      )}
    </BottomSheet>
  )
}
