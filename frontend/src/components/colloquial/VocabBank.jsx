// The topic's word bank: single words, grouped by category, under the phrase mosaic.
// Not the phrase list above it: these are vocabulary.arabic/transliteration/english entries
// a dialect writes on its own, independent of the spine's phrase slots.
import ArabicText from '../ui/ArabicText'
import Spelling from './Spelling'

function Group({ category, words }) {
  return (
    <div className="space-y-2">
      {category && (
        <p className="type-micro uppercase tracking-[0.18em] text-[var(--text-faint)]">{category}</p>
      )}
      <ul className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {words.map((word) => (
          <li
            key={word.arabic + word.english}
            className="flex flex-col gap-0.5 px-3 py-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]"
          >
            <ArabicText size="sm" className="text-[var(--text)]">{word.arabic}</ArabicText>
            <Spelling>{word.transliteration}</Spelling>
            <span className="type-small text-[var(--text-dim)]">{word.english}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

/** Vocabulary grouped by its `category`, uncategorised words first, in the order they were written. */
function grouped(vocabulary) {
  const order = []
  const by = new Map()
  for (const word of vocabulary) {
    const key = word.category || ''
    if (!by.has(key)) { by.set(key, []); order.push(key) }
    by.get(key).push(word)
  }
  return order.map((category) => ({ category, words: by.get(category) }))
}

export default function VocabBank({ vocabulary }) {
  if (!vocabulary?.length) return null
  return (
    <div className="space-y-5">
      {grouped(vocabulary).map(({ category, words }) => (
        <Group key={category || '_'} category={category} words={words} />
      ))}
    </div>
  )
}
