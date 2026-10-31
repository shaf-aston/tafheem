// A topic's single words as picture tiles, under their headings: after the
// phrases, the words a learner needs on their own. A word with no picture yet
// gets the same tinted tile a phrase does, so the grid never has holes.
import SpeakButton from '../../ui/SpeakButton'
import Face from '../parts/Face'
import Spelling from '../parts/Spelling'
import { grouped } from '../../../lib/colloquial/wordGroups'

export default function WordGrid({ words }) {
  let index = 0
  return (
    <div className="space-y-6">
      {grouped(words).map(([category, group]) => (
        <section key={category} className="space-y-2">
          {category && <h4 className="eyebrow text-[var(--text-faint)]">{category}</h4>}
          <ul className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2 sm:gap-3">
            {group.map((word) => (
              <li key={word.id} className="relative rounded-[var(--radius-md)] border border-[var(--border)] overflow-hidden">
                <Face phrase={word} index={index++} numbered={false} arabicSize="base" className="aspect-square" />
                <SpeakButton text={word.arabic} className="absolute top-1.5 end-1.5 bg-[var(--surface)]/80 backdrop-blur rounded-full" />
                <Spelling className="block text-center px-2 py-1 border-t border-[var(--border)]">{word.transliteration}</Spelling>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  )
}
