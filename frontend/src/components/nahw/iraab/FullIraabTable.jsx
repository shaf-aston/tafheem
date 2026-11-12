import { Fragment } from 'react'

import { UNNAMED, reading, caseFrom } from '../../../lib/nahw/grammarTerms'
import { roleVar } from '../../../lib/nahw/roleColors'
import BookPath from '../../grammar/BookPath'
import ArabicText from '../../ui/text/ArabicText'
import Disclosure from '../../ui/overlays/Disclosure'

/**
 * The click lives on the row, one handler on the table body; the keyboard lives
 * on each word, a real button, so Tab reaches it and Enter opens it.
 */
const NONE = UNNAMED

// The full table's columns: the ones every screen shows side by side, then the proof,
// which a phone moves under its row.
const BESIDE = [['الكلمة', 'Word'], ['الإعراب', 'Role · case · sign'], ['الجذر', 'Root'], ['العامل', 'Governed by']]
const PROOF = ['الدليل', 'Proof']

export default function FullIraabTable({ words, onRowClick }) {
  const pick = (e) => {
    const row = e.target.closest('tr[data-i]')
    if (row) onRowClick(words[Number(row.dataset.i)])
  }
  return (
    <Disclosure ruled label="Full table" hint="Every word, side by side" bodyClassName="pb-4 overflow-x-auto [direction:rtl]">
        {/* Right to left like the books: the word first, its proof last, and the scroll
            opens on the word. Case and sign sit under the role (one reading, one cell);
            a sign that only repeats مبني is dropped. A phone has no room for the proof
            beside the rest, so it takes its own line under the word's row. */}
        <table dir="rtl" className="w-full type-small border-collapse">
          <thead>
            <tr className="type-micro text-[var(--text-faint)] border-b border-[var(--border)] align-bottom">
              {[...BESIDE, PROOF].map(([ar, en]) => (
                <th key={en} className={`text-right font-normal py-2 px-3 ${en === PROOF[1] ? 'hidden md:table-cell' : ''}`}>
                  <ArabicText size="sm" className="block text-[var(--text-dim)]">{ar}</ArabicText>
                  <span dir="ltr" className="block">{en}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody onClick={pick}>
            {words.map((w, i) => {
              const said = reading(w)  // one reading of case and sign, the same the copied text prints
              const proof = (
                <>
                  <ArabicText size="sm" className="block leading-relaxed">{w.reason || NONE}</ArabicText>
                  {w.reason && <BookPath path={w.book} />}
                </>
              )
              return (
                <Fragment key={`${w.word}-${i}`}>
                <tr
                  data-i={i}
                  style={{ '--c': roleVar(w.role_key) }}
                  className="md:border-b border-[var(--border)] cursor-pointer align-top transition-colors
                    hover:bg-[var(--surface-hi)] role"
                >
                  <td className="py-3 px-3 whitespace-nowrap">
                    <ArabicText as="button" type="button" className="rounded-[var(--radius-sm)] px-1">{w.word}</ArabicText>
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    <ArabicText size="sm" className="block" style={{ color: 'var(--c)' }}>{w.name ?? (w.role || '–')}</ArabicText>
                    {said.length > 0 && (
                      <ArabicText size="tiny" className="block mt-1 text-[var(--text-dim)]">{said.join(' · ')}</ArabicText>
                    )}
                  </td>
                  <ArabicText as="td" size="sm" className="py-3 px-3 text-[var(--text-dim)] whitespace-nowrap">{w.root || NONE}</ArabicText>
                  <ArabicText as="td" size="sm" className="py-3 px-3 text-[var(--text-dim)] whitespace-nowrap">
                    {caseFrom(w) === undefined ? NONE : <>{w.governor == null && 'تابع لـ '}{words[caseFrom(w)].word}</>}
                  </ArabicText>
                  <td className="hidden md:table-cell py-3 px-3 text-[var(--text-dim)] min-w-[var(--layout-proof)]">{proof}</td>
                </tr>
                <tr data-i={i} className="md:hidden border-b border-[var(--border)] cursor-pointer">
                  <td colSpan={BESIDE.length} className="pb-3 px-3 text-[var(--text-dim)]">{proof}</td>
                </tr>
                </Fragment>
              )
            })}
          </tbody>
        </table>
    </Disclosure>
  )
}
