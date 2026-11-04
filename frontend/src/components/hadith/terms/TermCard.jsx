/**
 * One term of the science in a sheet: its Arabic and English name, what it meant in the language, what the science
 * means by it with the book's own sentence behind a disclosure, the terms it is often taken for (each, where both are in this group, with a table
 * of the group's questions, "—" where one side has no answer), and the hadith carrying it when it is a ruling.
 * Reads only the glossary it is handed (the usul guide); the hadith come from hadith/terms/TermHadith.
 */
import { useEffect, useRef } from 'react'

import ArabicText from '../../ui/text/ArabicText'
import BottomSheet from '../../ui/overlays/BottomSheet'
import SheetHeader from '../../ui/overlays/SheetHeader'
import TermQuote from './TermQuote'
import SheetLink from '../SheetLink'
import TermHadith from './TermHadith'
import { termAt } from './termsChart'

const Label = ({ children }) => (
  <h3 className="type-tiny uppercase tracking-[0.14em] text-[var(--text-faint)] mt-5 mb-2">{children}</h3>
)

/** Each question of the group that one of the two answers, each side's answer or "—": [{ id, q, here, there }]. */
const answersOf = (axes, here, there) =>
  axes
    .filter(({ id }) => here.answers?.[id] || there.answers?.[id])
    .map(({ id, q }) => ({ id, q, here: here.answers?.[id] ?? '—', there: there.answers?.[id] ?? '—' }))

export default function TermCard({ term, group, glossary, accent, onClose, onOpen, onTerm }) {
  const heading = useRef(null)
  // "Open X" swaps the card's content in place, so focus follows to the new name instead of falling to the page.
  useEffect(() => { heading.current?.focus() }, [term.arabic])
  const { arabic, en, lugha, meaning, quote, source, page, kind, confuse = [] } = term
  return (
    <BottomSheet label={en || arabic} onClose={onClose} className="max-h-[var(--sheet-tall)] flex flex-col">
      <SheetHeader onClose={onClose} align="start">
        <ArabicText as="h2" size="lg" ref={heading} tabIndex={-1} className="block m-0 leading-tight outline-none">{arabic}</ArabicText>
        <p className="type-ui font-semibold text-[var(--text)] m-0">{en}</p>
      </SheetHeader>
      <div key={arabic} className="overflow-y-auto px-5 pb-5">
        {lugha && (
          <>
            <Label>In the language</Label>
            <p className="type-body text-[var(--text-dim)] leading-relaxed m-0">{lugha}</p>
          </>
        )}
        <Label>In the science</Label>
        <p className="type-body text-[var(--text-dim)] leading-relaxed m-0">{meaning}</p>
        <TermQuote quote={quote} source={source} page={page} />
        {confuse.length > 0 && (
          <>
            <Label>Often confused with</Label>
            <ul className="m-0 p-0 list-none space-y-4">
              {confuse.map(({ arabic: other, why }) => {
                const found = termAt(glossary, other)
                // Only a pair from one group is set side by side: another group asks other questions.
                const rows = found?.group === group ? answersOf(group.axes ?? [], term, found.term) : []
                return (
                  <li key={other}>
                    <p className="m-0 flex items-baseline gap-2">
                      <ArabicText>{other}</ArabicText>
                      {found && <span className="type-ui font-medium text-[var(--text)]">{found.term.en}</span>}
                    </p>
                    <p className="type-body text-[var(--text-dim)] leading-relaxed m-0">{why}</p>
                    {rows.length > 0 && (
                      <table className="w-full mt-2 type-small border-collapse">
                        <thead>
                          <tr className="text-start text-[var(--text-faint)]">
                            <th scope="col" className="text-start font-normal py-1 pe-3" />
                            <th scope="col" className="text-start font-medium py-1 pe-3 text-[var(--text)]">{en}</th>
                            <th scope="col" className="text-start font-medium py-1 text-[var(--text)]">{found.term.en}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {rows.map(({ id, q, here, there }) => (
                            <tr key={id} className="border-t border-[var(--border)] align-top">
                              <th scope="row" className="text-start font-normal text-[var(--text-faint)] py-1.5 pe-3">{q}</th>
                              <td className="py-1.5 pe-3 text-[var(--text-dim)]">{here}</td>
                              <td className="py-1.5 text-[var(--text-dim)]">{there}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                    {found && onTerm && <SheetLink accent={accent} onClick={() => onTerm(found.term.arabic)}>Open {found.term.en}</SheetLink>}
                  </li>
                )
              })}
            </ul>
          </>
        )}
        {kind && (
          <>
            <Label>Hadith carrying this ruling</Label>
            <TermHadith kind={kind} accent={accent} onOpen={onOpen} />
          </>
        )}
      </div>
    </BottomSheet>
  )
}
