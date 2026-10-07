// A topic's single words (not phrases), grouped by category in written order.
import ArabicText from '../ui/ArabicText'
import Spelling from './Spelling'

function grouped(words) {
  const by = new Map()
  for (const w of words) by.set(w.category ?? '', [...(by.get(w.category ?? '') ?? []), w])
  return [...by]
}

export default function VocabBank({ vocabulary }) {
  return (
    <div className="space-y-5">
      {grouped(vocabulary).map(([category, words]) => (
        <div key={category} className="space-y-2">
          {category && <p className="type-micro uppercase tracking-[0.18em] text-[var(--text-faint)]">{category}</p>}
          <ul className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {words.map((w) => (
              <li key={w.arabic} className="flex flex-col gap-0.5 px-3 py-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
                <ArabicText size="sm" className="text-[var(--text)]">{w.arabic}</ArabicText>
                <Spelling>{w.transliteration}</Spelling>
                <span className="type-small text-[var(--text-dim)]">{w.english}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
