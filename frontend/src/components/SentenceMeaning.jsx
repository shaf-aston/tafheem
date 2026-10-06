/**
 * A phrase or sentence asked of the dictionary: its sense, then word by word,
 * the way al-Maany sets the two out. The sense sits in the card with the
 * Arabic, as the ayah view's translation does; the words sit under it, each one
 * a way into its own dictionary entry.
 */
import ArabicText from './ui/ArabicText'
import { GoButton } from './ui/RootActions'
import SourceBadge from './ui/SourceBadge'
import TranslationStrip from './ui/TranslationStrip'

export default function SentenceMeaning({ data, accent, onGo, onLookup }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <p className="text-[var(--text-dim)] type-body capitalize">{data.kind}</p>
        {data.ref && onGo && (
          <GoButton onClick={() => onGo('quran', data.ref)} style={{ '--c': accent }}>
            Open ayah {data.ref}
          </GoButton>
        )}
      </div>

      <div className="rise-in rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)] overflow-hidden">
        <ArabicText as="p" size="lg" className="p-5 text-[var(--text)]">{data.query}</ArabicText>
        <TranslationStrip source={data.source}>
          {data.meaning
            ? <p className="type-body text-[var(--text)] leading-relaxed">{data.meaning}</p>
            : <p className="type-body text-[var(--text-dim)]">The translator could not be reached, so only the words below.</p>}
        </TranslationStrip>
      </div>
      {data.left_out?.length > 0 && (
        <p className="type-small text-[var(--text-dim)]">Left out, not Arabic: {data.left_out.join(', ')}</p>
      )}

      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h3 className="text-sm text-[var(--text-dim)]">Word by word</h3>
        <SourceBadge source={data.words_source} />
      </div>
      <div className="flex flex-wrap justify-center gap-2" dir="rtl">
        {data.words.map((w, i) => (
          <button
            key={i}
            type="button"
            onClick={() => onLookup(w.base)}
            title={`Look up ${w.base}`}
            style={{ '--i': i }}
            className="word rise-in flex flex-col items-center gap-1 p-2.5 rounded-[var(--radius-md)]
              bg-[var(--surface)] border border-[var(--border)] transition-colors hover:border-[var(--text-faint)]"
          >
            <ArabicText className="text-[var(--text)] leading-tight">{w.arabic}</ArabicText>
            <span className="type-small text-[var(--text-dim)] max-w-[7rem] text-center" lang="en" dir="ltr">
              {w.english}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
