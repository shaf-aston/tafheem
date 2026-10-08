/**
 * What classical books say of this hadith, quoted and never put in our words: for each ruling the sort of book it
 * is in (label), the scholar, the question an 'Ilal answer answers (asked), his own sentence (cut to a few lines, the rest
 * one press away; quote_label says what a remark is) and the book and page.
 * A book that gives only a chapter heading shows that. The hadith is matched to the book's entry by its wording
 * and its narrators, so the group says "possible".
 */
import ArabicText from './ArabicText'
import ShowRest from './ShowRest'

export default function ScholarRulings({ rulings, accent }) {
  if (!rulings.length) return null
  return (
    <section aria-labelledby="scholar-rulings" className="mt-4 pt-4 border-t border-[var(--border)]">
      <h3 id="scholar-rulings" className="type-small font-semibold text-[var(--text-dim)] m-0">Possible: scholars on this hadith</h3>
      <p className="type-tiny m-0 mt-1 mb-3 text-[var(--text-faint)]">Found by its wording and its narrators, so it may be another narration of it.</p>
      <ul className="list-none m-0 p-0 space-y-4">
        {rulings.map((r) => (
          <li key={`${r.kind}${r.scholar}${r.page}${r.quote}${r.asked}`} className="space-y-1.5">
            <p className="type-small m-0 text-[var(--text-dim)]">{r.label}</p>
            {r.scholar && <ArabicText as="p" size="sm" className="block m-0 text-[var(--text)]">{r.scholar}</ArabicText>}
            {r.chapter && <ArabicText as="p" size="sm" className="block m-0 text-[var(--text-dim)]">{r.chapter}</ArabicText>}
            {r.asked && (
              <div className="space-y-0.5">
                <p className="type-tiny m-0 text-[var(--text-faint)]">The question</p>
                <ShowRest lines={3} accent={accent}>
                  <ArabicText as="p" size="sm" className="block m-0 leading-loose text-[var(--text-dim)]">{r.asked}</ArabicText>
                </ShowRest>
              </div>
            )}
            {r.quote && (
              <div className="space-y-0.5">
                {r.quote_label && <p className="type-tiny m-0 text-[var(--text-faint)]">{r.quote_label}</p>}
                <ShowRest lines={5} accent={accent}>
                  <ArabicText as="p" size="sm" className="block m-0 leading-loose text-[var(--text)]">{r.quote}</ArabicText>
                </ShowRest>
              </div>
            )}
            <p className="type-tiny m-0 text-[var(--text-faint)]">{[r.source, r.page].filter(Boolean).join(', ')}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}
