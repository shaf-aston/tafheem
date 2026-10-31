/**
 * A classical book's entry on a narrator (Tahdhib al-Kamal and the like) set
 * as sunnah.com sets it: his full name bold at the top, paragraphs, a heading
 * such as روى عن over the rows under it, each row's book letters (خ م د ت س ق)
 * as small marks that name their book on hover, and a scholar quoted in the
 * accent with his words after. The words are the book's own, never changed.
 *
 * An entry from a build that kept no lines (`blocks` empty) shows its plain text.
 */
import { withoutButton } from '../../../lib/hadith/rijal'

import ArabicText from '../../ui/text/ArabicText'

function Run({ run, accent }) {
  if (run.role === 'mark') {
    return (
      <span
        title={run.title || undefined}
        className="inline-block mx-0.5 px-1.5 rounded-full border border-[var(--border)] text-[var(--text-dim)] text-[0.8em] leading-normal align-middle"
      >
        {run.t}
      </span>
    )
  }
  if (run.role === 'scholar') return <span className="font-medium" style={{ color: accent }}>{run.t}</span>
  if (run.role === 'verdict') return <span className="text-[var(--text)]">{run.t}</span>
  return run.t
}

const LINE = {
  title: 'block m-0 font-bold text-[var(--text)]',
  para: 'block m-0 text-[var(--text-dim)]',
  label: 'block m-0 mt-3 font-bold text-[var(--text)]',
  item: 'block m-0 text-[var(--text-dim)]',
}

export default function ClassicalText({ text, accent }) {
  if (!text.blocks?.length) {
    return <ArabicText as="p" size="sm" className="block m-0 whitespace-pre-line text-[var(--text-dim)]">{withoutButton(text.body)}</ArabicText>
  }
  // The key to the book letters, each as the page names it; a letter the page gives no name is left out, never guessed.
  const key = new Map(text.blocks.flatMap((b) => b.runs).filter((r) => r.role === 'mark' && r.title).map((r) => [r.t, r.title]))
  return (
    <div dir="rtl" className="space-y-1.5">
      {text.blocks.map((b, i) => (
        <ArabicText key={i} as="p" size="sm" className={LINE[b.kind] ?? LINE.para}>
          {b.runs.map((r, j) => <Run key={j} run={r} accent={accent} />)}
        </ArabicText>
      ))}
      {key.size > 0 && (
        <p dir="ltr" className="m-0 pt-3 type-small text-[var(--text-faint)] flex flex-wrap gap-x-4 gap-y-1">
          {[...key].map(([mark, book]) => (
            <span key={mark}><Run run={{ t: mark, role: 'mark' }} /> {book}</span>
          ))}
        </p>
      )}
    </div>
  )
}
